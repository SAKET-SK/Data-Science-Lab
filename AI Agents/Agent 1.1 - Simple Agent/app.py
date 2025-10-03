import streamlit as st
from datetime import datetime
import time

# ADD CREWAI IMPORTS
from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM and Agents
llm = LLM(
    model=os.getenv("OPENROUTER_MODEL"),
    temperature=0.7,
    api_key=os.getenv("OPENROUTER_API_KEY")
)

researcher = Agent(
    role="AI Researcher",
    goal="Analyze emerging AI trends",
    backstory="Analyst who studies AI daily.",
    llm=llm
)

writer = Agent(
    role="Technical Writer",
    goal="Explain AI trends in simple language",
    backstory="Writes for developers and non-tech readers.",
    llm=llm
)

st.set_page_config(
    page_title="AI Trends Analyzer",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False
if 'researcher_status' not in st.session_state:
    st.session_state.researcher_status = 'ready'
if 'writer_status' not in st.session_state:
    st.session_state.writer_status = 'ready'
if 'result' not in st.session_state:
    st.session_state.result = None
if 'analysis_count' not in st.session_state:
    st.session_state.analysis_count = 0

# Minimal safe CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Hero section - simple version
st.markdown("""
<div style="text-align: center; padding: 2rem; color: white;">
    <h1>🔮 AI Trends Analyzer</h1>
    <p>Discover and understand emerging AI trends</p>
</div>
""", unsafe_allow_html=True)

# White content box
st.markdown('<div style="background: white; padding: 2rem; border-radius: 20px; margin: 2rem; color: black">', unsafe_allow_html=True)

# Agent status
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background: #f0f0f0; padding: 1rem; border-radius: 10px; border-left: 5px solid #667eea;">
        <h3 style="color:black">🔍 AI Researcher</h3>
        <p style="color:black">Status: <strong>{st.session_state.researcher_status.upper()}</strong></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: #f0f0f0; padding: 1rem; border-radius: 10px; border-left: 5px solid #667eea;">
        <h3 style="color:black">📝 Technical Writer</h3>
        <p style="color:black">Status: <strong>{st.session_state.writer_status.upper()}</strong></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Analyses Completed", st.session_state.analysis_count)
with col2:
    st.metric("Active Agents", "2")
with col3:
    st.metric("Avg Time", "~45s")

st.markdown("---")

# Input section
st.subheader("🎯 What AI trend would you like to explore?")

topic_input = st.text_area(
    "Topic Input",
    placeholder="Example: Latest developments in Large Language Models, AI in healthcare...",
    height=100,
    label_visibility="collapsed"
)

# Advanced options
with st.expander("⚙️ Advanced Options"):
    col_a, col_b = st.columns(2)
    with col_a:
        depth = st.select_slider(
            "Analysis Depth",
            options=["Quick Overview", "Standard", "Deep Dive"],
            value="Standard"
        )
    with col_b:
        audience = st.selectbox(
            "Target Audience",
            ["Developers", "Business Leaders", "General Public", "Researchers"]
        )
    
    include_sources = st.checkbox("Include source references", value=True)
    include_examples = st.checkbox("Include practical examples", value=True)

# Analyze button
if st.button("🚀 Analyze This Trend", disabled=st.session_state.analyzing or not topic_input, type="primary"):
    st.session_state.analyzing = True
    # Don't rerun here - let execution happen below

# REPLACED: Demo execution with REAL CrewAI execution
if st.session_state.analyzing:
    st.session_state.researcher_status = 'working'
    st.session_state.writer_status = 'waiting'
    
    st.info("🔄 Starting analysis...")
    
    try:
        # Create tasks
        research_task = Task(
            description=f"Research and analyze: {topic_input}. Depth: {depth}",
            agent=researcher,
            expected_output="Detailed research findings"
        )
        
        write_task = Task(
            description=f"Write analysis for {audience}. Examples: {include_examples}. Sources: {include_sources}",
            agent=writer,
            expected_output="Clear article"
        )
        
        # Show spinner and run crew
        with st.spinner("🤖 Agents are collaborating... This may take 30-60 seconds"):
            # Run crew
            crew = Crew(
                agents=[researcher, writer],
                tasks=[research_task, write_task],
                process=Process.sequential,
                verbose=True  # This will show output in terminal
            )
            
            result = crew.kickoff()
            st.session_state.result = str(result)
            
            # DEBUG
            st.write("✅ Crew finished!")
            st.write(f"Result length: {len(str(result))} characters")
        
        st.session_state.researcher_status = 'complete'
        st.session_state.writer_status = 'complete'
        st.success("✅ Analysis complete!")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.error("Check your .env file has OPENAI_API_KEY set correctly")
        st.session_state.researcher_status = 'ready'
        st.session_state.writer_status = 'ready'
    
    # Reset analyzing flag
    st.session_state.analyzing = False
    st.session_state.analysis_count += 1

# Display results
if st.session_state.result:
    st.markdown("---")
    st.success("✨ Analysis Complete!")
    
    # Create a visible result container
    st.markdown("""
    <div style="background: #f8f9fa; padding: 2rem; border-radius: 15px; margin: 1rem 0; border: 2px solid #667eea;">
        <h3 style="color: #667eea; margin-top: 0;">📄 Generated Analysis Report</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Display result in a container with visible background
    with st.container():
        st.markdown(st.session_state.result)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Download Result",
            st.session_state.result,
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col2:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.result = None
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)