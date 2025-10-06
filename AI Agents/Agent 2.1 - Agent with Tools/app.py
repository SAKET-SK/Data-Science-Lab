import streamlit as st
from datetime import datetime
import time

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai_tools import EXASearchTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize EXA Search Tool
try:
    Exa_Search_Tool = EXASearchTool()
except Exception as e:
    st.error(f"Error initializing EXA Search Tool: {e}")
    Exa_Search_Tool = None

# Page config
st.set_page_config(
    page_title="Script Generator Studio",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'generating' not in st.session_state:
    st.session_state.generating = False
if 'explorer_status' not in st.session_state:
    st.session_state.explorer_status = 'ready'
if 'writer_status' not in st.session_state:
    st.session_state.writer_status = 'ready'
if 'script_result' not in st.session_state:
    st.session_state.script_result = None
if 'script_count' not in st.session_state:
    st.session_state.script_count = 0

# Custom CSS - Theatrical theme
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .curtain-header {
        background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%);
        padding: 3rem 2rem;
        border-radius: 0 0 30px 30px;
        position: relative;
        box-shadow: 0 10px 30px rgba(220, 20, 60, 0.3);
    }
    
    .curtain-header::before,
    .curtain-header::after {
        content: "🎭";
        position: absolute;
        font-size: 3rem;
        opacity: 0.3;
    }
    
    .curtain-header::before {
        left: 20px;
        top: 20px;
    }
    
    .curtain-header::after {
        right: 20px;
        top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Theatrical header
st.markdown("""
<div class="curtain-header">
    <h1 style="color: white; text-align: center; margin: 0; font-size: 3rem;">
        🎭 Script Generator Studio
    </h1>
    <p style="color: rgba(255,255,255,0.9); text-align: center; font-size: 1.2rem; margin-top: 1rem;">
        Transform research into theatrical conversations
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# White content box
st.markdown('<div style="background: white; padding: 2rem; border-radius: 20px; margin: 2rem; color: black">', unsafe_allow_html=True)

# Agent status cards
st.markdown("### 🎬 Your Creative Crew")
col1, col2 = st.columns(2)

with col1:
    explorer_icon = "🔍" if st.session_state.explorer_status == 'ready' else "⚡" if st.session_state.explorer_status == 'working' else "✅"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 12px; color: white;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">{explorer_icon}</span>
            <div>
                <h3 style="margin: 0; color: white;">Content Explorer</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Gathering latest information</p>
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; 
                             border-radius: 15px; font-size: 0.85rem; display: inline-block; margin-top: 0.5rem;">
                    {st.session_state.explorer_status.upper()}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    writer_icon = "📝" if st.session_state.writer_status == 'ready' else "✍️" if st.session_state.writer_status == 'working' else "✅"
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 1.5rem; border-radius: 12px; color: white;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <span style="font-size: 2rem;">{writer_icon}</span>
            <div>
                <h3 style="margin: 0; color: white;">Script Writer</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Crafting theatrical dialogue</p>
                <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; 
                             border-radius: 15px; font-size: 0.85rem; display: inline-block; margin-top: 0.5rem;">
                    {st.session_state.writer_status.upper()}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Scripts Generated", st.session_state.script_count)
with col2:
    st.metric("Active Agents", "2")
with col3:
    st.metric("Script Length", "~200 words")

st.markdown("---")

# Input section
st.subheader("🎯 What topic should we script?")

topic_input = st.text_input(
    "Topic",
    placeholder="Example: GTA 6, SpaceX Starship, iPhone 16, Climate Summit...",
    label_visibility="collapsed"
)

# Style options
with st.expander("🎨 Script Customization"):
    col_a, col_b = st.columns(2)
    with col_a:
        script_style = st.selectbox(
            "Writing Style",
            ["Shakespearean", "Modern Casual", "News Reporter", "Comedy Duo", "Documentary"]
        )
        word_count = st.slider("Word Count", 100, 500, 200, 50)
    
    with col_b:
        conversation_type = st.selectbox(
            "Conversation Type",
            ["Dialogue (2 people)", "Monologue", "Interview", "Debate"]
        )
        humor_level = st.select_slider(
            "Humor Level",
            options=["Serious", "Light", "Moderate", "Very Funny", "Comedy"]
        )
    
    include_stage_directions = st.checkbox("Include stage directions", value=True)

# Generate button
if st.button("🎬 Generate Script", disabled=st.session_state.generating or not topic_input, type="primary"):
    st.session_state.generating = True

# CREWAI EXECUTION
if st.session_state.generating:
    st.markdown("---")
    st.subheader("🎭 Production in Progress")
    
    st.session_state.explorer_status = 'working'
    st.session_state.writer_status = 'waiting'
    
    # Explorer working indicator
    st.markdown("""
    <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; 
                border-left: 4px solid #2196f3; margin: 1rem 0;">
        <p style="color: #1565c0; margin: 0;">🔍 <strong>Content Explorer</strong> is researching the topic...</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Get current date
        Today = datetime.now().strftime("%d-%b-%Y")
        
        # Define agents
        content_explorer = Agent(
            role='content explorer',
            goal='Gather and provide latest information about the topic from internet',
            llm='openrouter/openai/gpt-oss-20b:free',
            backstory=f'You are an expert researcher who can gather detailed information about a topic. Gather at least 10 information points. Today is {Today}',
            tools=[Exa_Search_Tool] if Exa_Search_Tool else [],
            cache=True,
            max_iter=5
        )
        
        Script_Writer = Agent(
            role='Script Writer',
            goal='Create an interesting conversational script',
            llm='openrouter/openai/gpt-oss-20b:free',
            verbose=True,
            backstory=f'You are an expert in {script_style} writing. Create a {conversation_type} script in approximately {word_count} words. Humor level: {humor_level}. {"Include stage directions." if include_stage_directions else "No stage directions."} Today is {Today}'
        )
        
        # Define tasks
        get_details = Task(
            description=f"Get latest, trending, interesting information and news about {topic_input}",
            expected_output=f"Latest news, interesting information and trivia about {topic_input}",
            agent=content_explorer
        )
        
        create_script = Task(
            description=f"Create an engaging {conversation_type} in {script_style} style about the researched information. Make it approximately {word_count} words. Humor level: {humor_level}.",
            expected_output=f"A well-structured conversational script connecting key details",
            agent=Script_Writer,
            context=[get_details]
        )
        
        # Create and run crew
        crew = Crew(
            agents=[content_explorer, Script_Writer],
            tasks=[get_details, create_script],
            verbose=True,
            process=Process.sequential
        )
        
        with st.spinner("🔄 Agents are collaborating... This may take 30-90 seconds"):
            result = crew.kickoff(inputs={'topic': topic_input})
            st.session_state.script_result = str(result)
        
        st.session_state.explorer_status = 'complete'
        st.session_state.writer_status = 'complete'
        
        st.success("🎉 Script generation complete!")
        
    except Exception as e:
        st.error(f"❌ Error during generation: {str(e)}")
        st.error("Make sure your .env file has OPENROUTER_API_KEY and EXA_API_KEY set correctly")
        st.session_state.explorer_status = 'ready'
        st.session_state.writer_status = 'ready'
    
    st.session_state.generating = False
    st.session_state.script_count += 1
    st.session_state.explorer_status = 'ready'
    st.session_state.writer_status = 'ready'
    time.sleep(1)
    st.rerun()

# Display script
if st.session_state.script_result:
    st.markdown("---")
    
    # Script display with theatrical styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%); 
                padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
        <h3 style="color: white; margin: 0; text-align: center;">📜 Your Generated Script</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Script content in a "script paper" style box
    st.markdown(f"""
    <div style="background: #fffef0; color: black; padding: 2rem; border-radius: 10px; 
                border: 2px solid #ddd; margin: 1rem 0; 
                font-family: 'Courier New', monospace;
                box-shadow: 5px 5px 15px rgba(0,0,0,0.1);">
        <pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; color: #333; margin: 0;">
{st.session_state.script_result}
        </pre>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Download Script",
            st.session_state.script_result,
            file_name=f"script_{topic_input.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        if st.button("📋 Show for Copy", use_container_width=True):
            st.code(st.session_state.script_result, language=None)
    with col3:
        if st.button("🔄 New Script", use_container_width=True):
            st.session_state.script_result = None
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: white;">
    <p style="font-size: 0.9rem; opacity: 0.9;">🎭 Powered by CrewAI • Using EXA Search & DeepSeek</p>
</div>
""", unsafe_allow_html=True)