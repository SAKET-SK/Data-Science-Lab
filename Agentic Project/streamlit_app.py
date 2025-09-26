# streamlit_app.py

"""
Streamlit UI for Automated Test Case Generation System
Provides a web interface for the RAG-based test case generator
"""

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import sys

# Add the scripts directory to Python path to import backend modules
sys.path.append('scripts')

try:
    # Import your existing backend functions
    from test_case_generator import (
        generate_test_cases_with_rag,
        general_rag_answer,
        create_excel_from_response,
        find_excel_chunks,
        find_workflow_chunks,
        engine,
        DB_SCHEMA
    )
    from sqlalchemy import text
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False
    st.error(f"Backend import failed: {e}")

# Page configuration
st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: black;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .status-success {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
    }
    .status-error {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
    }
    .status-info {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
    }
    ul, li{
            color: black;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧪 Automated Test Case Generation System</h1>
        <p>RAG-Powered Test Case Generator with Excel Export</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not BACKEND_AVAILABLE:
        st.error("Backend functions not available. Please ensure test_case_generator.py is in the scripts/ folder.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Mode",
        ["🏠 Home", "🧪 Generate Test Cases", "💬 RAG Query", "📊 Repository Stats", "⚙️ Settings"]
    )
    
    # Database status in sidebar
    with st.sidebar:
        st.markdown("### System Status")
        check_database_status()
    
    # Route to different pages
    if page == "🏠 Home":
        show_home_page()
    elif page == "🧪 Generate Test Cases":
        show_test_generation_page()
    elif page == "💬 RAG Query":
        show_rag_query_page()
    elif page == "📊 Repository Stats":
        show_repository_stats()
    elif page == "⚙️ Settings":
        show_settings_page()

def check_database_status():
    """Check and display database connection status"""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {DB_SCHEMA}, public"))
            result = conn.execute(text("SELECT COUNT(*) FROM vector_documents"))
            total = result.fetchone()[0]
            
            excel_result = conn.execute(text("SELECT COUNT(*) FROM vector_documents WHERE file_type = 'excel'"))
            excel_count = excel_result.fetchone()[0]
            
            word_result = conn.execute(text("SELECT COUNT(*) FROM vector_documents WHERE file_type = 'word'"))
            word_count = word_result.fetchone()[0]
            
            st.success(f"✅ Database Connected")
            st.info(f"📄 Total chunks: {total}")
            st.info(f"📊 Excel chunks: {excel_count}")
            st.info(f"📝 Word chunks: {word_count}")
            
    except Exception as e:
        st.error(f"❌ Database Error")
        st.error(str(e))

def show_home_page():
    """Display home page with system overview"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3 style="color: black">🎯 Key Features</h3>
            <ul>
                <li><strong>RAG-Powered Generation</strong>: Uses your Excel templates and Word documents</li>
                <li><strong>Intelligent Analysis</strong>: Understands context and generates relevant test cases</li>
                <li><strong>Excel Export</strong>: Creates formatted Excel files with proper styling</li>
                <li><strong>Flexible Generation</strong>: Adaptive number of scenarios and test cases</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3 style="color: black">🚀 Quick Start</h3>
            <ol>
                <li>Navigate to <strong>Generate Test Cases</strong></li>
                <li>Describe what you want to test</li>
                <li>Click <strong>Generate</strong></li>
                <li>Download your formatted Excel file</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    
    if os.path.exists("test_cases"):
        files = [f for f in os.listdir("test_cases") if f.endswith('.xlsx')]
        if files:
            # Sort by modification time
            files_with_time = [(f, os.path.getmtime(f"test_cases/{f}")) for f in files]
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            
            recent_files = files_with_time[:5]
            
            for filename, timestamp in recent_files:
                file_time = datetime.fromtimestamp(timestamp)
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"📁 {filename}")
                with col2:
                    st.write(f"🕐 {file_time.strftime('%Y-%m-%d %H:%M')}")
                with col3:
                    if st.button("📥", key=f"download_{filename}"):
                        with open(f"test_cases/{filename}", "rb") as file:
                            st.download_button(
                                label="Download",
                                data=file.read(),
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
        else:
            st.info("No test case files generated yet. Start by creating your first test cases!")

def show_test_generation_page():
    """Display test case generation interface"""
    
    st.header("🧪 Generate Test Cases")
    
    # Input section
    st.subheader("📝 Test Requirements")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_request = st.text_area(
            "Describe what test cases you need:",
            placeholder="Example: Generate test cases for user login functionality with password validation",
            height=120,
            help="Be specific about the functionality you want to test. Include modules, features, or specific requirements."
        )
    
    with col2:
        st.markdown("### 💡 Tips for Better Results")
        st.info("""
        - Be specific about the module/feature
        - Mention the type of testing (UI, API, etc.)
        - Include any special requirements
        - Reference specific workflows if needed
        """)
    
    # Generation options
    st.subheader("⚙️ Generation Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_rag_context = st.checkbox("Show RAG Context", value=False, help="Display the RAG response used for generation")
    
    with col2:
        show_full_response = st.checkbox("Show Full AI Response", value=False, help="Display the complete AI response")
    
    with col3:
        custom_filename = st.text_input("Custom filename (optional)", placeholder="my_test_cases")
    
    # Generate button
    if st.button("🚀 Generate Test Cases", type="primary", use_container_width=True):
        if not user_request.strip():
            st.error("Please enter a test case requirement description.")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Generate test cases
            status_text.text("🔍 Analyzing requirements and generating test cases...")
            progress_bar.progress(25)
            
            with st.spinner("Generating test cases using RAG context..."):
                ai_response = generate_test_cases_with_rag(user_request)
            
            progress_bar.progress(75)
            status_text.text("📊 Creating Excel file...")
            
            # Step 2: Create Excel file
            filename_prefix = custom_filename if custom_filename.strip() else "automated_test_cases"
            filepath, count = create_excel_from_response(ai_response, filename_prefix)
            
            progress_bar.progress(100)
            status_text.text("✅ Generation complete!")
            
            # Success message
            st.markdown("""
            <div class="status-success">
                <h4 style="color: black">✅ Test Cases Generated Successfully!</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Results summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Test Cases Generated", count)
            with col2:
                st.metric("File Size", f"{os.path.getsize(filepath) / 1024:.1f} KB")
            with col3:
                st.metric("Generation Time", "< 2 min")
            
            # Download section
            st.subheader("📥 Download Results")
            
            with open(filepath, "rb") as file:
                st.download_button(
                    label="📥 Download Excel File",
                    data=file.read(),
                    file_name=os.path.basename(filepath),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            
            # Optional displays
            if show_rag_context:
                st.subheader("🔍 RAG Context Used")
                with st.expander("View RAG Context"):
                    try:
                        from test_case_generator import find_similar_chunks_general
                        chunks = find_similar_chunks_general(user_request)
                        for similarity, doc_name, chunk_text in chunks:
                            st.write(f"**From {doc_name}** (Similarity: {similarity:.2%})")
                            st.write(chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text)
                            st.write("---")
                    except Exception as e:
                        st.error(f"Could not retrieve RAG context: {e}")
            
            if show_full_response:
                st.subheader("🤖 AI Response")
                with st.expander("View Full AI Response"):
                    st.text_area("Raw Response", ai_response, height=300)
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("")
            st.markdown(f"""
            <div class="status-error">
                <h4>❌ Generation Failed</h4>
                <p>Error: {str(e)}</p>
            </div>
            """, unsafe_allow_html=True)

def show_rag_query_page():
    """Display RAG query interface"""
    
    st.header("💬 RAG Document Query")
    st.write("Ask questions about your documents to understand what information is available for test case generation.")
    
    user_question = st.text_area(
        "Ask a question about your documents:",
        placeholder="Example: What functionality is described in the leave management document?",
        height=100
    )
    
    if st.button("🔍 Search Documents", type="primary"):
        if not user_question.strip():
            st.error("Please enter a question.")
            return
        
        with st.spinner("Searching documents..."):
            try:
                answer = general_rag_answer(user_question)
                
                st.subheader("💡 Answer")
                st.write(answer)
                
                # Show source chunks
                st.subheader("📚 Source Information")
                try:
                    from test_case_generator import find_similar_chunks_general
                    chunks = find_similar_chunks_general(user_question)
                    
                    for i, (similarity, doc_name, chunk_text) in enumerate(chunks, 1):
                        with st.expander(f"Source {i}: {doc_name} (Relevance: {similarity:.1%})"):
                            st.write(chunk_text)
                            
                except Exception as e:
                    st.error(f"Could not retrieve source chunks: {e}")
                    
            except Exception as e:
                st.error(f"Query failed: {str(e)}")

def show_repository_stats():
    """Display repository statistics and management"""
    
    st.header("📊 Repository Statistics")
    
    try:
        # Test cases folder stats
        if os.path.exists("test_cases"):
            files = [f for f in os.listdir("test_cases") if f.endswith('.xlsx')]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Generated Files", len(files))
            
            if files:
                total_size = sum(os.path.getsize(f"test_cases/{f}") for f in files)
                with col2:
                    st.metric("Total Size", f"{total_size / 1024 / 1024:.1f} MB")
                
                latest_file = max(files, key=lambda x: os.path.getmtime(f"test_cases/{x}"))
                latest_time = datetime.fromtimestamp(os.path.getmtime(f"test_cases/{latest_file}"))
                with col3:
                    st.metric("Latest Generation", latest_time.strftime("%Y-%m-%d"))
        
        # Document repository stats
        st.subheader("📄 Document Repository")
        
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {DB_SCHEMA}, public"))
            
            # Total documents
            result = conn.execute(text("SELECT COUNT(*) FROM vector_documents"))
            total_docs = result.fetchone()[0]
            
            # By file type
            result = conn.execute(text("""
                SELECT file_type, COUNT(*) 
                FROM vector_documents 
                GROUP BY file_type
            """))
            type_stats = result.fetchall()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Document Chunks", total_docs)
                
                # File type breakdown
                type_data = {"File Type": [], "Count": []}
                for file_type, count in type_stats:
                    type_data["File Type"].append(file_type or "Unknown")
                    type_data["Count"].append(count)
                
                if type_data["File Type"]:
                    df = pd.DataFrame(type_data)
                    st.bar_chart(df.set_index("File Type"))
            
            with col2:
                # Recent activity
                st.subheader("📁 File Management")
                
                if os.path.exists("test_cases") and files:
                    st.write("Recent files:")
                    
                    for filename in files[-5:]:  # Show last 5 files
                        file_path = f"test_cases/{filename}"
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        col_name, col_time, col_action = st.columns([3, 2, 1])
                        
                        with col_name:
                            st.write(f"📄 {filename}")
                        with col_time:
                            st.write(file_time.strftime("%m-%d %H:%M"))
                        with col_action:
                            if st.button("🗑️", key=f"del_{filename}", help="Delete file"):
                                try:
                                    os.remove(file_path)
                                    st.success(f"Deleted {filename}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Delete failed: {e}")
                
                # Cleanup button
                if st.button("🧹 Clean Old Files", help="Delete files older than 30 days"):
                    cleanup_old_files()
        
    except Exception as e:
        st.error(f"Could not load repository stats: {str(e)}")

def show_settings_page():
    """Display settings and configuration"""
    
    st.header("⚙️ System Settings")
    
    # System Information
    st.subheader("🔧 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Backend Status:** ✅ Connected")
        st.info(f"**Database Schema:** {DB_SCHEMA}")
        st.info("**Output Directory:** test_cases/")
    
    with col2:
        # Environment variables (safe ones)
        st.write("**Configuration:**")
        st.write(f"- Model: {os.getenv('MODEL_NAME', 'mistral:7b')}")
        st.write(f"- Database: {os.getenv('DB_NAME', 'Not set')}")
    
    # File management
    st.subheader("📁 File Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Refresh Stats"):
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Session"):
            st.cache_data.clear()
            st.success("Session reset complete")
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        st.write("**Model Settings:**")
        st.slider("Response Timeout", 30, 300, 120, help="Timeout for AI model responses (seconds)")
        st.selectbox("Output Format", ["Excel (.xlsx)", "CSV (.csv)"], help="Default output format")
        
        st.write("**Generation Settings:**")
        st.checkbox("Enable detailed logging", help="Log detailed generation process")
        st.checkbox("Auto-cleanup old files", help="Automatically delete files older than 30 days")

def cleanup_old_files():
    """Clean up files older than 30 days"""
    import time
    
    if not os.path.exists("test_cases"):
        return
    
    current_time = time.time()
    deleted_count = 0
    
    for filename in os.listdir("test_cases"):
        file_path = f"test_cases/{filename}"
        file_age = current_time - os.path.getmtime(file_path)
        
        # Delete files older than 30 days (30 * 24 * 60 * 60 seconds)
        if file_age > 30 * 24 * 60 * 60:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                st.error(f"Could not delete {filename}: {e}")
    
    if deleted_count > 0:
        st.success(f"Deleted {deleted_count} old files")
    else:
        st.info("No old files to delete")

if __name__ == "__main__":
    main()
