import streamlit as st
from datetime import datetime
import time

# ============================================================================
# 🔧 CREWAI SETUP - ADD YOUR ACTUAL AGENTS HERE
# ============================================================================

from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import ChatOpenAI  # or your LLM provider

import os
from dotenv import load_dotenv
load_dotenv()

llm = LLM(
    model = os.getenv("OPENROUTER_MODEL"),
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY"),
    temperature = 0.3
)

# Initialize your LLM
# llm = ChatOpenAI(
#     model="gpt-4",  # or your model
#     api_key="your-api-key"  # or use environment variable
# )


# Your agents
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

# ============================================================================

# Page config
st.set_page_config(
    page_title="AI Trends Analyzer",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero section */
    .hero {
        text-align: center;
        padding: 4rem 2rem 2rem 2rem;
        color: white;
    }
    
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(to right, #fff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeInDown 0.8s ease;
    }
    
    .hero p {
        font-size: 1.3rem;
        margin-top: 1rem;
        opacity: 0.95;
        animation: fadeInUp 0.8s ease;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Main content card */
    .content-card {
        background: white;
        border-radius: 24px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 1200px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        animation: slideUp 0.6s ease;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Agent cards */
    .agent-card {
        background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
    }
    
    .agent-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .agent-icon {
        font-size: 2rem;
    }
    
    .agent-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }
    
    .agent-role {
        color: #64748b;
        font-size: 0.95rem;
        margin: 0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .status-ready {
        background: #e0e7ff;
        color: #4f46e5;
    }
    
    .status-working {
        background: #fef3c7;
        color: #d97706;
        animation: pulse 2s infinite;
    }
    
    .status-complete {
        background: #d1fae5;
        color: #059669;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Input section */
    .input-section {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 16px;
        margin: 2rem 0;
    }
    
    /* Output section */
    .output-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 2rem 0;
        color: white;
    }
    
    .output-content {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 12px;
        color: #1e293b;
        margin-top: 1rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Progress indicators */
    .progress-step {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        border-radius: 12px;
        border-left: 4px solid #cbd5e1;
        transition: all 0.3s ease;
    }
    
    .progress-step.active {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }
    
    .progress-step.complete {
        border-left-color: #10b981;
        background: #f0fdf4;
    }
    
    .step-icon {
        font-size: 1.5rem;
    }
    
    .step-text {
        flex: 1;
    }
    
    .step-title {
        font-weight: 600;
        color: #1e293b;
        margin: 0;
    }
    
    .step-desc {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Stats */
    .stat-box {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
        border-radius: 12px;
        margin: 0.5rem;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    
    .stat-label {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

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

# Hero section
st.markdown("""
<div class="hero">
    <h1>🔮 AI Trends Analyzer</h1>
    <p>Discover and understand emerging AI trends with intelligent agent collaboration</p>
</div>
""", unsafe_allow_html=True)

# Main content
st.markdown('<div class="content-card">', unsafe_allow_html=True)

# Agent status cards
col1, col2 = st.columns(2)

with col1:
    researcher_icon = "🔍" if st.session_state.researcher_status == 'ready' else "⚡" if st.session_state.researcher_status == 'working' else "✅"
    st.markdown(f"""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">{researcher_icon}</span>
            <div>
                <h3 class="agent-name">AI Researcher</h3>
                <p class="agent-role">Analyzing emerging AI trends</p>
            </div>
        </div>
        <span class="status-badge status-{st.session_state.researcher_status}">
            {st.session_state.researcher_status.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    writer_icon = "📝" if st.session_state.writer_status == 'ready' else "✍️" if st.session_state.writer_status == 'working' else "✅"
    st.markdown(f"""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">{writer_icon}</span>
            <div>
                <h3 class="agent-name">Technical Writer</h3>
                <p class="agent-role">Explaining trends in simple language</p>
            </div>
        </div>
        <span class="status-badge status-{st.session_state.writer_status}">
            {st.session_state.writer_status.upper()}
        </span>
    </div>
    """, unsafe_allow_html=True)

# Stats
st.markdown("### 📊 Quick Stats")
stat_col1, stat_col2, stat_col3 = st.columns(3)

with stat_col1:
    st.markdown(f"""
    <div class="stat-box">
        <p class="stat-number">{st.session_state.analysis_count}</p>
        <p class="stat-label">Analyses Completed</p>
    </div>
    """, unsafe_allow_html=True)

with stat_col2:
    st.markdown("""
    <div class="stat-box">
        <p class="stat-number">2</p>
        <p class="stat-label">Active Agents</p>
    </div>
    """, unsafe_allow_html=True)

with stat_col3:
    avg_time = "~45s" if st.session_state.analysis_count > 0 else "N/A"
    st.markdown(f"""
    <div class="stat-box">
        <p class="stat-number">{avg_time}</p>
        <p class="stat-label">Avg. Analysis Time</p>
    </div>
    """, unsafe_allow_html=True)

# Input section
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.markdown("### 🎯 What AI trend would you like to explore?")

topic_input = st.text_area(
    "",
    placeholder="Example: Latest developments in Large Language Models, AI in healthcare, Autonomous agents, Edge AI...",
    height=100,
    label_visibility="collapsed"
)

# Optional parameters
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

st.markdown('</div>', unsafe_allow_html=True)

# Analyze button
if st.button("🚀 Analyze This Trend", disabled=st.session_state.analyzing or not topic_input):
    st.session_state.analyzing = True
    st.rerun()

# ============================================================================
# 🚀 CREW EXECUTION - REPLACE THIS SECTION WITH YOUR ACTUAL CREW
# ============================================================================
if st.session_state.analyzing:
    st.markdown("---")
    st.markdown("### 🔄 Analysis in Progress")
    
    progress_container = st.container()
    
    with progress_container:
        # Show researcher working
        st.markdown(f"""
        <div class="progress-step active">
            <span class="step-icon">🔍</span>
            <div class="step-text">
                <p class="step-title">AI Researcher is analyzing...</p>
                <p class="step-desc">Gathering insights on {topic_input[:50]}...</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.researcher_status = 'working'
        
        # ====================================================================
        # 🔧 REPLACE THIS SIMULATION WITH YOUR ACTUAL CREWAI CODE:
        # ====================================================================
        
        # Create your tasks
        task1 = Task(
            description="Find 3 new trends in AI in 2025.",
            expected_output="3 clear bullet points.",
            agent=researcher
        )

        task2 = Task(
            description="Write a newsletter about those 3 trends.",
            expected_output="3-paragraph readable article.",
            agent=writer
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[researcher, writer],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute with progress indicator
        with st.spinner("🔍 Researcher analyzing trends..."):
            result = crew.kickoff()
        
        # Store the result
        st.session_state.result = str(result)
        
        
        # ====================================================================
        # 📝 DEMO MODE (Remove this when using actual CrewAI)
        # ====================================================================
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        st.session_state.researcher_status = 'complete'
        
        st.markdown("""
        <div class="progress-step complete">
            <span class="step-icon">✅</span>
            <div class="step-text">
                <p class="step-title">Research Complete</p>
                <p class="step-desc">Found key trends and emerging patterns</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(0.5)
        
        # Show writer working
        st.markdown("""
        <div class="progress-step active">
            <span class="step-icon">✍️</span>
            <div class="step-text">
                <p class="step-title">Technical Writer is crafting...</p>
                <p class="step-desc">Converting insights into clear, accessible content</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.writer_status = 'working'
        progress_bar2 = st.progress(0)
        
        for i in range(100):
            time.sleep(0.02)
            progress_bar2.progress(i + 1)
        
        st.session_state.writer_status = 'complete'
        
        st.markdown("""
        <div class="progress-step complete">
            <span class="step-icon">✅</span>
            <div class="step-text">
                <p class="step-title">Writing Complete</p>
                <p class="step-desc">Analysis ready for review</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate demo result (REPLACE WITH: st.session_state.result from crew.kickoff())
        st.session_state.result = f"""# AI Trend Analysis: {topic_input}

## Executive Summary
{topic_input} represents a significant shift in the AI landscape. Our analysis reveals three critical developments that developers and organizations should monitor closely.

## Key Findings

### 1. Current State
The technology has matured significantly over the past 12 months, with major breakthroughs in efficiency and accessibility. Industry adoption rates have increased by 340%, indicating strong market validation.

### 2. Emerging Patterns
- **Performance Improvements**: New architectures are achieving 5x better efficiency
- **Cost Reduction**: Operating costs have decreased by 60% year-over-year
- **Accessibility**: Lower barriers to entry for developers and small teams

### 3. Future Trajectory
Experts predict this trend will fundamentally reshape how we approach AI development. The next 18 months are critical for establishing best practices and standards.

## Technical Deep Dive

### Architecture Evolution
Recent innovations focus on modular, composable systems that allow for greater flexibility. This represents a departure from monolithic approaches.

### Implementation Considerations
For {audience.lower()}:
- Start with pilot projects to understand capabilities
- Invest in team training and knowledge building  
- Build robust monitoring and evaluation frameworks

## Business Impact

### For Enterprises
This trend offers opportunities for competitive differentiation. Early adopters are seeing 25-40% improvements in key metrics.

### For Startups
Lower entry barriers mean increased competition but also more opportunities for innovation in niche applications.

## Practical Examples

1. **E-commerce**: Personalization engines using this approach show 35% better engagement
2. **Healthcare**: Diagnostic tools achieving 92% accuracy in clinical trials
3. **Finance**: Fraud detection systems with 99.7% precision rates

## Recommendations

**Short-term (0-6 months)**
- Evaluate current capabilities against organizational needs
- Run proof-of-concept projects
- Build internal expertise

**Medium-term (6-18 months)**  
- Scale successful pilots to production
- Establish governance frameworks
- Integrate with existing systems

**Long-term (18+ months)**
- Develop proprietary implementations
- Contribute to open-source ecosystems
- Lead industry standards development

## Conclusion

{topic_input} is not just a trend—it's becoming a fundamental building block of modern AI systems. Organizations that invest strategically now will be well-positioned for the next wave of AI innovation.

---
*Analysis generated by AI Researcher & Technical Writer collaboration*
*Depth: {depth} | Audience: {audience}*
"""
        # ====================================================================
    
    # Update states and rerun
    st.session_state.analyzing = False
    st.session_state.analysis_count += 1
    st.session_state.researcher_status = 'ready'
    st.session_state.writer_status = 'ready'
    time.sleep(0.5)
    st.rerun()

# Display results
if st.session_state.result:
    st.markdown("---")
    st.markdown('<div class="output-section">', unsafe_allow_html=True)
    st.markdown("### ✨ Analysis Complete!")
    st.markdown('<div class="output-content">', unsafe_allow_html=True)
    st.markdown(st.session_state.result)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download button
    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
    with col_dl1:
        st.download_button(
            "📄 Download as Markdown",
            st.session_state.result,
            file_name=f"ai_trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            "📋 Copy as Text",
            st.session_state.result,
            file_name=f"ai_trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl3:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.result = None
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 3rem 2rem; color: white;">
    <p style="font-size: 0.9rem; opacity: 0.9;">Powered by CrewAI • Built with ❤️</p>
</div>
""", unsafe_allow_html=True)