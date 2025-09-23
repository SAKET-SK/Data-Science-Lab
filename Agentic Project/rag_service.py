# rag_system.py

"""
Simple RAG system - Ask questions about your documents!
Uses your vector_documents table and Mistral AI model.

Author(s): Saket Khopkar
"""

import os
import requests
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_huggingface import HuggingFaceEmbeddings

# ----------------------------
# SETUP
# ----------------------------
load_dotenv()

# Database connection
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_SCHEMA = os.getenv("DB_SCHEMA", "qpot")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# AI settings
OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral:7b")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ----------------------------
# MAIN FUNCTIONS
# ----------------------------

def find_similar_chunks(question):
    """Find document chunks similar to the question"""
    try:
        # Convert question to numbers
        question_vector = np.array(embeddings.embed_query(question))
        
        # Get chunks from database
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {DB_SCHEMA}, public"))
            result = conn.execute(text("SELECT doc_name, chunk_text, embedding FROM vector_documents WHERE embedding IS NOT NULL"))
            
            similar_chunks = []
            for row in result:
                doc_name, chunk_text, embedding = row
                
                try:
                    # Convert string embedding to numpy array
                    if isinstance(embedding, str):
                        # Remove brackets and split by comma
                        embedding_str = embedding.strip('[]')
                        embedding_list = [float(x.strip()) for x in embedding_str.split(',')]
                        embedding_vector = np.array(embedding_list)
                    elif isinstance(embedding, list):
                        embedding_vector = np.array(embedding)
                    else:
                        embedding_vector = np.array(embedding)
                    
                    # Calculate similarity (higher = more similar)
                    dot_product = np.dot(question_vector, embedding_vector)
                    norm1 = np.linalg.norm(question_vector)
                    norm2 = np.linalg.norm(embedding_vector)
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        similar_chunks.append((similarity, doc_name, chunk_text))
                
                except Exception as calc_error:
                    print(f"Skipping chunk due to embedding error: {calc_error}")
                    continue
            
            # Return top 3 most similar chunks
            similar_chunks.sort(reverse=True)
            print(f"Found {len(similar_chunks)} valid chunks")
            return similar_chunks[:3]
    
    except Exception as e:
        print(f"Error finding chunks: {e}")
        return []

def ask_ai(context, question):
    """Send question with context to AI model"""
    try:
        prompt = f"""Answer the question based only on this information:

{context}

Question: {question}
Answer:"""
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'No answer received')
        else:
            return f"AI Error: {response.status_code}"
    
    except Exception as e:
        return f"Error asking AI: {e}"

def rag_answer(user_question):
    """Main function: Get answer using your documents"""
    print("Searching your documents...")
    
    # Step 1: Find similar document chunks
    chunks = find_similar_chunks(user_question)
    
    if not chunks:
        return "Sorry, couldn't find relevant information in your documents."
    
    # Step 2: Build context from chunks
    context = "Relevant information from your documents:\n\n"
    sources = []
    
    for similarity, doc_name, chunk_text in chunks:
        context += f"From {doc_name}:\n{chunk_text}\n\n"
        if doc_name not in sources:
            sources.append(doc_name)
    
    # Step 3: Ask AI
    print("Getting AI response...")
    answer = ask_ai(context, user_question)
    
    # Step 4: Add sources
    answer += f"\n\nSources: {', '.join(sources)}"
    
    return answer

# ----------------------------
# SIMPLE INTERFACE
# ----------------------------

def check_database():
    """Check what's in the database"""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {DB_SCHEMA}, public"))
            
            # Count total chunks
            result = conn.execute(text("SELECT COUNT(*) FROM vector_documents"))
            total = result.fetchone()[0]
            print(f"Total chunks in database: {total}")
            
            # Count chunks with embeddings
            result = conn.execute(text("SELECT COUNT(*) FROM vector_documents WHERE embedding IS NOT NULL"))
            with_embeddings = result.fetchone()[0]
            print(f"Chunks with embeddings: {with_embeddings}")
            
            # Show sample chunk
            result = conn.execute(text("SELECT doc_name, LEFT(chunk_text, 100), embedding FROM vector_documents WHERE embedding IS NOT NULL LIMIT 1"))
            sample = result.fetchone()
            if sample:
                doc_name, text_preview, embedding = sample
                print(f"Sample chunk from {doc_name}: {text_preview}...")
                print(f"Embedding type: {type(embedding)}")
                if embedding:
                    if hasattr(embedding, '__len__'):
                        print(f"Embedding length: {len(embedding)}")
            
    except Exception as e:
        print(f"Database check error: {e}")

def main():
    print("Simple RAG System Ready!")
    print("Ask questions about your documents\n")
    
    # Check database first
    print("Checking database...")
    check_database()
    print()
    
    # Start asking questions
    while True:
        question = input("Your question (or 'quit' to exit): ")
        
        if question.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break
        
        if question.strip():
            answer = rag_answer(question)
            print(f"\nAnswer:\n{answer}\n")
            print("-" * 50)

if __name__ == "__main__":
    main()
