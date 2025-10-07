import streamlit as st
from datetime import datetime
import time

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai_tools import EXASearchTool
import os
from dotenv import load_dotenv
import finnhub
import json
from datetime import datetime
from langchain_community.tools import DuckDuckGoSearchRun

# Current date for context
Now = datetime.now()
Today = Now.strftime("%d-%b-%Y")

# Load environment variables
load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# Simple cache implementation


# This cache system below helps you avoid making repeated expensive operations, like:

# - Calling an external API repeatedly (e.g., stock market, search tools)
# - Processing the same data multiple times
# - Saving time & cost by storing recent results for reuse

cache = {}
cache_expiry = {}

def get_cached_data(key, expiry_seconds=300):
    """Get data from cache if not expired."""
    if key in cache and time.time() < cache_expiry.get(key, 0):
        return cache[key]
    return None

def set_cached_data(key, data, expiry_seconds=300):
    """Set data in cache with expiry time."""
    cache[key] = data
    cache_expiry[key] = time.time() + expiry_seconds

# Define a web search tool
@tool("DuckDuckGo Search")
def search_tool(search_query: str):
    """Search the internet for information on a given topic"""
    return DuckDuckGoSearchRun().run(search_query)

# Setting up CrewAI custom tools
@tool("Get current stock price")
def get_current_stock_price(symbol: str) -> str:
    """Use this function to get the current stock price for a given symbol.

    Args:
        symbol (str): The stock symbol. For Indian stocks, use format like 'RELIANCE.NS' or 'TCS.BO'.

    Returns:
        str: The current stock price or error message.
    """
    """Use this function to get the current stock price..."""
    cache_key = f"price_{symbol}"
    cached_result = get_cached_data(cache_key, 60)  # Cache for 60 seconds
    if cached_result:
        return cached_result

    try:
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)

        # Handle Indian stock exchange symbols
        api_symbol = symbol
        if '.NSE' in symbol or '.BSE' in symbol:
            # Finnhub requires different format for Indian stocks
            # Strip the .NSE or .BSE and add the exchange info
            base_symbol = symbol.split('.')[0]
            exchange = symbol.split('.')[1]
            # For some Indian exchanges, you might need to modify the symbol format
            api_symbol = f"{base_symbol}:{exchange}"

        # Get the quote
        quote = finnhub_client.quote(api_symbol)

        if quote and 'c' in quote:
            current_price = quote['c']
            set_cached_data(cache_key, str(current_price))  # Cache the result
            return f"{current_price:.2f}"
        else:
            return f"Could not fetch current price for {symbol}"
    except Exception as e:
        return f"Error fetching current price for {symbol}: {e}"

@tool
def get_company_info(symbol: str):
    """Use this function to get company information and current financial snapshot for a given stock symbol.

    Args:
        symbol (str): The stock symbol. For Indian stocks, use format like 'RELIANCE.NS' or 'TCS.BO'.

    Returns:
        JSON containing company profile and current financial snapshot.
    """
    try:
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)

        api_symbol = symbol
        if '.NSE' in symbol or '.BSE' in symbol:
            # Finnhub requires different format for Indian stocks
            # Strip the .NSE or .BSE and add the exchange info
            base_symbol = symbol.split('.')[0]
            exchange = symbol.split('.')[1]
            # For some Indian exchanges, you might need to modify the symbol format
            api_symbol = f"{base_symbol}:{exchange}"

        # Get company profile
        profile = finnhub_client.company_profile2(symbol=api_symbol)

        # Get quote data
        quote = finnhub_client.quote(api_symbol)

        # Get basic financials
        financials = finnhub_client.company_basic_financials(api_symbol, 'all')

        # Create a cleaned info dictionary
        company_info_cleaned = {
            "Name": profile.get("name"),
            "Symbol": profile.get("ticker"),
            "Current Stock Price": f"{quote.get('c')} {profile.get('currency', 'USD')}",
            "Market Cap": profile.get("marketCapitalization"),
            "Sector": profile.get("finnhubIndustry"),
            "Industry": profile.get("finnhubIndustry"),
            "Country": profile.get("country"),
            "Exchange": profile.get("exchange"),
            "IPO": profile.get("ipo"),
            "Logo": profile.get("logo"),
            "Website": profile.get("weburl"),
        }

        # Add financial metrics if available
        if financials and 'metric' in financials:
            metrics = financials['metric']
            company_info_cleaned.update({
                "52 Week Low": metrics.get("52WeekLow"),
                "52 Week High": metrics.get("52WeekHigh"),
                "P/E Ratio": metrics.get("peBasicExclExtraTTM"),
                "EPS": metrics.get("epsBasicExclExtraItemsTTM"),
                "Dividend Yield": metrics.get("dividendYieldIndicatedAnnual"),
                "ROE": metrics.get("roeTTM"),
                "ROA": metrics.get("roaTTM"),
                "Debt to Equity": metrics.get("totalDebtOverTotalEquityQuarterly"),
                "Revenue Growth": metrics.get("revenueGrowthTTMYoy"),
            })

        return json.dumps(company_info_cleaned)
    except Exception as e:
        return f"Error fetching company profile for {symbol}: {e}"

@tool
def get_income_statements(symbol: str):
    """Use this function to get income statements for a given stock symbol.

    Args:
        symbol (str): The stock symbol. For Indian stocks, use format like 'RELIANCE.NS' or 'TCS.BO'.

    Returns:
        JSON containing income statements or an empty dictionary.
    """
    try:
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)

        # Handle Indian stock exchange symbols
        api_symbol = symbol
        if '.NSE' in symbol or '.BSE' in symbol:
            # Finnhub requires different format for Indian stocks
            # Strip the .NSE or .BSE and add the exchange info
            base_symbol = symbol.split('.')[0]
            exchange = symbol.split('.')[1]
            # For some Indian exchanges, you might need to modify the symbol format
            api_symbol = f"{base_symbol}:{exchange}"

        # Get financial statements
        financials = finnhub_client.financials_reported(symbol=api_symbol, freq='annual')

        # Extract income statements if available
        if financials and 'data' in financials and len(financials['data']) > 0:
            income_statements = []
            for report in financials['data']:
                if 'report' in report and 'ic' in report['report']:
                    income_statements.append({
                        'year': report.get('year'),
                        'quarter': report.get('quarter'),
                        'income_statement': report['report']['ic']
                    })
            return json.dumps(income_statements)
        else:
            return f"No income statements found for {symbol}"
    except Exception as e:
        return f"Error fetching income statements for {symbol}: {e}"
    

# Page config
st.set_page_config(
    page_title="StockSense AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False
if 'news_status' not in st.session_state:
    st.session_state.news_status = 'ready'
if 'data_status' not in st.session_state:
    st.session_state.data_status = 'ready'
if 'analyst_status' not in st.session_state:
    st.session_state.analyst_status = 'ready'
if 'expert_status' not in st.session_state:
    st.session_state.expert_status = 'ready'
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'analysis_count' not in st.session_state:
    st.session_state.analysis_count = 0

# Custom CSS - Money Green Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background: #0a0e27;
        color: #e0e0e0;
    }
    
    /* Animated ticker tape */
    @keyframes ticker {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .ticker-tape {
        background: linear-gradient(90deg, #00695c 0%, #00c853 100%);
        padding: 0.8rem;
        overflow: hidden;
        white-space: nowrap;
        box-shadow: 0 4px 15px rgba(0, 200, 83, 0.3);
    }
    
    .ticker-content {
        display: inline-block;
        animation: ticker 30s linear infinite;
        color: white;
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
    }
    
    /* Main header */
    .money-header {
        background: linear-gradient(135deg, #00695c 0%, #00c853 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        position: relative;
        box-shadow: 0 10px 40px rgba(0, 200, 83, 0.4);
        margin: 2rem 0;
    }
    
    .money-header h1 {
        color: white;
        margin: 0;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .money-header p {
        color: rgba(255,255,255,0.95);
        margin-top: 0.5rem;
        font-size: 1.2rem;
    }
    
    /* Dollar symbols decoration */
    .money-header::before {
        content: "💰";
        position: absolute;
        font-size: 4rem;
        opacity: 0.2;
        left: 20px;
        top: 10px;
    }
    
    .money-header::after {
        content: "📈";
        position: absolute;
        font-size: 4rem;
        opacity: 0.2;
        right: 20px;
        top: 10px;
    }
    
    /* Content box */
    .content-box {
        background: #1a1f3a;
        padding: 2rem;
        border-radius: 20px;
        border: 2px solid #00c853;
        box-shadow: 0 0 30px rgba(0, 200, 83, 0.2);
    }
    
    /* Agent cards */
    .agent-card {
        background: linear-gradient(135deg, #1a3a2e 0%, #1a4a3a 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #00c853;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .agent-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00c853, #ffd700);
    }
    
    .agent-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 200, 83, 0.4);
        border-color: #ffd700;
    }
    
    .agent-icon {
        font-size: 2.5rem;
        filter: drop-shadow(0 0 10px #00c853);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        font-family: 'Roboto Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .status-ready {
        background: #00695c;
        color: #e0f2f1;
        box-shadow: 0 0 15px rgba(0, 200, 83, 0.3);
    }
    
    .status-working {
        background: #ffd700;
        color: #1a1f3a;
        animation: pulse 1.5s infinite;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
    }
    
    .status-complete {
        background: #00c853;
        color: white;
        box-shadow: 0 0 20px rgba(0, 200, 83, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a3a2e 0%, #00695c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #00c853;
        text-align: center;
        box-shadow: 0 5px 20px rgba(0, 200, 83, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00c853;
        font-family: 'Roboto Mono', monospace;
        text-shadow: 0 0 10px rgba(0, 200, 83, 0.5);
    }
    
    .metric-label {
        color: #e0f2f1;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Recommendation badge */
    .rec-badge-buy {
        background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
        color: white;
        padding: 1.5rem 3rem;
        border-radius: 15px;
        font-size: 2rem;
        font-weight: 700;
        box-shadow: 0 10px 40px rgba(0, 200, 83, 0.6);
        animation: glow-green 2s infinite;
    }
    
    .rec-badge-hold {
        background: linear-gradient(135deg, #ffd700 0%, #ffeb3b 100%);
        color: #1a1f3a;
        padding: 1.5rem 3rem;
        border-radius: 15px;
        font-size: 2rem;
        font-weight: 700;
        box-shadow: 0 10px 40px rgba(255, 215, 0, 0.6);
    }
    
    .rec-badge-sell {
        background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
        color: white;
        padding: 1.5rem 3rem;
        border-radius: 15px;
        font-size: 2rem;
        font-weight: 700;
        box-shadow: 0 10px 40px rgba(244, 67, 54, 0.6);
        animation: glow-red 2s infinite;
    }
    
    @keyframes glow-green {
        0%, 100% { box-shadow: 0 10px 40px rgba(0, 200, 83, 0.6); }
        50% { box-shadow: 0 15px 50px rgba(0, 200, 83, 0.9); }
    }
    
    @keyframes glow-red {
        0%, 100% { box-shadow: 0 10px 40px rgba(244, 67, 54, 0.6); }
        50% { box-shadow: 0 15px 50px rgba(244, 67, 54, 0.9); }
    }
    
    /* Price display */
    .price-display {
        background: #0a0e27;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #00c853;
        font-family: 'Roboto Mono', monospace;
    }
    
    .price-value {
        font-size: 3rem;
        color: #00c853;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 200, 83, 0.7);
    }
    
    .price-change-positive {
        color: #00c853;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .price-change-negative {
        color: #f44336;
        font-size: 1.5rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Animated ticker tape
st.markdown("""
<div class="ticker-tape">
    <div class="ticker-content">
        💰 NASDAQ +0.85% • S&P 500 +1.23% • DOW +245.67 • NIFTY 50 +0.92% • SENSEX +185.45 • GOLD ₹65,340 • 
        CRUDE $82.45 • USD/INR ₹83.12 • BTC $45,230 • ETH $2,890 • RELIANCE ₹2,845 • TCS ₹3,678 💰
    </div>
</div>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="money-header">
    <h1>💰 StockSense AI</h1>
    <p>AI-Powered Market Intelligence & Investment Advisor</p>
</div>
""", unsafe_allow_html=True)

# Content box start
st.markdown('<div class="content-box">', unsafe_allow_html=True)

# Agent status display
st.markdown("### 🤖 AI Agent Crew")

col1, col2, col3, col4 = st.columns(4)

agents_info = [
    {
        "col": col1,
        "icon": "📰" if st.session_state.news_status == 'ready' else "⚡" if st.session_state.news_status == 'working' else "✅",
        "name": "News Researcher",
        "role": "Latest Company News",
        "status": st.session_state.news_status
    },
    {
        "col": col2,
        "icon": "📊" if st.session_state.data_status == 'ready' else "⚡" if st.session_state.data_status == 'working' else "✅",
        "name": "Data Researcher",
        "role": "Financial Data",
        "status": st.session_state.data_status
    },
    {
        "col": col3,
        "icon": "🔬" if st.session_state.analyst_status == 'ready' else "⚡" if st.session_state.analyst_status == 'working' else "✅",
        "name": "Data Analyst",
        "role": "Analysis & Insights",
        "status": st.session_state.analyst_status
    },
    {
        "col": col4,
        "icon": "💼" if st.session_state.expert_status == 'ready' else "⚡" if st.session_state.expert_status == 'working' else "✅",
        "name": "Financial Expert",
        "role": "Buy/Hold/Sell",
        "status": st.session_state.expert_status
    }
]

for agent in agents_info:
    with agent["col"]:
        st.markdown(f"""
        <div class="agent-card">
            <div style="text-align: center;">
                <div class="agent-icon">{agent['icon']}</div>
                <h4 style="color: #00c853; margin: 0.5rem 0;">{agent['name']}</h4>
                <p style="color: #b0bec5; font-size: 0.85rem; margin: 0.5rem 0;">{agent['role']}</p>
                <span class="status-badge status-{agent['status']}">{agent['status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Stats
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{st.session_state.analysis_count}</div>
        <div class="metric-label">Analyses Done</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">4</div>
        <div class="metric-label">AI Agents</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-value">~2min</div>
        <div class="metric-label">Avg Time</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Input section
st.markdown("### 📈 Enter Stock Symbol")

col_input, col_market = st.columns([3, 1])

with col_input:
    stock_symbol = st.text_input(
        "Stock Symbol",
        placeholder="e.g., AAPL, RELIANCE.NSE, TCS.BSE, GOOGL",
        label_visibility="collapsed"
    )

with col_market:
    market_hint = st.selectbox(
        "Market",
        ["🇺🇸 US Stock", "🇮🇳 Indian NSE", "🇮🇳 Indian BSE"],
        label_visibility="collapsed"
    )

st.markdown("""
<div style="background: #1a3a2e; padding: 1rem; border-radius: 10px; border-left: 4px solid #00c853; margin: 1rem 0;">
    <p style="color: #e0f2f1; margin: 0; font-size: 0.9rem;">
        💡 <strong>Examples:</strong> AAPL (Apple), RELIANCE.NSE (Reliance Industries), TCS.BSE (Tata Consultancy)
    </p>
</div>
""", unsafe_allow_html=True)

# Analyze button
if st.button("💰 Analyze Stock", disabled=st.session_state.analyzing or not stock_symbol, type="primary"):
    st.session_state.analyzing = True

# Analysis execution
if st.session_state.analyzing:
    
    # Define agents
    # Agent for gathering company news and information
    news_info_explorer = Agent(
        role='News and Info Researcher',
        goal='Gather and provide the latest news and information about a company from the internet',
        #llm='gpt-4o',
        #llm='openrouter/deepseek/deepseek-chat-v3-0324:free',
        llm='openrouter/openai/gpt-oss-20b:free',
        verbose=True,
        backstory=(
            'You are an expert researcher, who can gather detailed information about a company. '
            'Consider you are on: ' + Today
        ),
        tools=[search_tool],
        cache=True,
        max_iter=5,
    )

    # Agent for gathering financial data
    data_explorer = Agent(
        role='Data Researcher',
        goal='Gather and provide financial data and company information about a stock',
        #llm='gpt-4o',
        llm='openrouter/openai/gpt-oss-20b:free',
        verbose=True,
        backstory=(
            'You are an expert researcher, who can gather detailed information about a company or stock. '
            'For Indian stocks, use format like "RELIANCE.NSE" for NSE or "TCS.BSE" for BSE. '
            'Intelligently figure out it is an Indian or US stock'
            'For US stocks, just use the ticker symbol like "AAPL". '
            'Use Indian units for numbers (lakh, crore) for Indian stocks only. '
            'Consider you are on: ' + Today
        ),
        tools=[get_company_info, get_income_statements],
        cache=True,
        max_iter=5,
    )

    # Agent for analyzing data
    analyst = Agent(
        role='Data Analyst',
        goal='Consolidate financial data, stock information, and provide a summary',
        #llm='gpt-4o',
        llm='openrouter/openai/gpt-oss-20b:free',
        verbose=True,
        backstory=(
            'You are an expert in analyzing financial data, stock/company-related current information, and '
            'making a comprehensive analysis. Use Indian units for numbers (lakh, crore). '
            'Consider you are on: ' + Today
        ),
    )

    # Agent for financial recommendations
    fin_expert = Agent(
        role='Financial Expert',
        goal='Considering financial analysis of a stock, make investment recommendations',
        #llm='gpt-4o',
        llm='openrouter/openai/gpt-oss-20b:free',
        verbose=True,
        tools=[get_current_stock_price],
        max_iter=5,
        backstory=(
            'You are an expert financial advisor who can provide investment recommendations. '
            'Consider the financial analysis, current information about the company, current stock price, '
            'and make recommendations about whether to buy/hold/sell a stock along with reasons. '
            'For Indian stocks, use format like "RELIANCE.NSE" for NSE or "TCS.BSE" for BSE. '
            'For US stocks, just use the ticker symbol like "AAPL". '
            'Intelligently figure out it is an Indian or US stock. '
            'Use Indian units for numbers (lakh, crore) for Indian stocks only. '
            'Consider you are on: ' + Today
        ),
    )

    # Define Tasks
    # Task to gather financial data of a stock
    get_company_financials = Task(
        description="Get key financial data for stock: {stock}. Focus on the most important metrics only.",
        expected_output="Summary of key financial metrics for {stock}. Keep it concise and under 1000 words.",
        agent=data_explorer,
    )

    # Task to gather company news
    get_company_news = Task(
        description="Get latest 3-5 important news items about company: {stock}",
        expected_output="Brief summary of 3-5 latest significant news items. Keep it under 800 words.",
        agent=news_info_explorer,
    )

    # Task to analyze financial data and news
    analyse = Task(
        description="Analyze the financial data and news, focusing on the most important points.",
        expected_output="Concise analysis of the stock's key metrics and news impact. Maximum 1500 words.",
        agent=analyst,
        context=[get_company_financials, get_company_news],
        output_file='Analysis.md',
    )

    # Task to provide financial advice
    advise = Task(
        description="Make a recommendation about investing in a stock, based on analysis provided and current stock price. "
                    "Explain the reasons.",
        expected_output="Recommendation (Buy / Hold / Sell) of a stock backed with reasons elaborated."
                    "Response in Mark down format.",
        agent=fin_expert,
        context=[analyse],
        output_file='Recommendation.md',
    )

    # Callback function to print a timestamp
    def timestamp(Input):
        print(datetime.now())

    # Define the crew with agents and tasks in sequential process
    crew = Crew(
        agents=[data_explorer, news_info_explorer, analyst, fin_expert],
        tasks=[get_company_financials, get_company_news, analyse, advise],
        verbose=True,
        Process=Process.sequential,
        step_callback=timestamp,
    )

    result = crew.kickoff(inputs={'stock': stock_symbol})
    # print("Final Result:", result)

    st.markdown("---")
    st.markdown("### ⚡ Analysis in Progress")


    
    # Simulate agent workflow
    progress_bar = st.progress(0)
    
    # News Researcher
    st.session_state.news_status = 'working'
    st.markdown("""
    <div style="background: #1a3a2e; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffd700; margin: 1rem 0;">
        <p style="color: #ffd700; margin: 0;">📰 <strong>News Researcher</strong> gathering latest company news...</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Searching news..."):
        time.sleep(2)
        progress_bar.progress(25)
    st.session_state.news_status = 'complete'
    
    # Data Researcher
    st.session_state.data_status = 'working'
    st.markdown("""
    <div style="background: #1a3a2e; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffd700; margin: 1rem 0;">
        <p style="color: #ffd700; margin: 0;">📊 <strong>Data Researcher</strong> pulling financial data...</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Fetching financials..."):
        time.sleep(2)
        progress_bar.progress(50)
    st.session_state.data_status = 'complete'
    
    # Analyst
    st.session_state.analyst_status = 'working'
    st.markdown("""
    <div style="background: #1a3a2e; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffd700; margin: 1rem 0;">
        <p style="color: #ffd700; margin: 0;">🔬 <strong>Data Analyst</strong> analyzing data...</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Crunching numbers..."):
        time.sleep(2)
        progress_bar.progress(75)
    st.session_state.analyst_status = 'complete'
    
    # Financial Expert
    st.session_state.expert_status = 'working'
    st.markdown("""
    <div style="background: #1a3a2e; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffd700; margin: 1rem 0;">
        <p style="color: #ffd700; margin: 0;">💼 <strong>Financial Expert</strong> making recommendations...</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Generating advice..."):
        time.sleep(2)
        progress_bar.progress(100)
    st.session_state.expert_status = 'complete'
    
    # Store demo result
    st.session_state.analysis_result = {
        "recommendation": "BUY",  # or "HOLD" or "SELL"
        "current_price": "₹2,845.50" if "NSE" in stock_symbol or "BSE" in stock_symbol else "$175.43",
        "change": "+2.45%",
        "summary": f"Strong fundamentals with positive growth outlook for {stock_symbol}."
    }
    
    st.session_state.analyzing = False
    st.session_state.analysis_count += 1
    st.success("✅ Analysis Complete!")
    time.sleep(1)
    st.rerun()

# Display results
if st.session_state.analysis_result:
    st.markdown("---")
    
    result = st.session_state.analysis_result
    
    # Recommendation badge
    rec_class = f"rec-badge-{result['recommendation'].lower()}"
    rec_icon = "🚀" if result['recommendation'] == "BUY" else "⏸️" if result['recommendation'] == "HOLD" else "⚠️"
    
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <div class="{rec_class}">
            {rec_icon} {result['recommendation']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Price and metrics
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown(f"""
        <div class="price-display">
            <p style="color: #b0bec5; margin: 0; font-size: 1rem;">Current Price</p>
            <div class="price-value">{result['current_price']}</div>
            <div class="price-change-positive">▲ {result['change']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_p2:
        st.markdown(f"""
        <div class="price-display">
            <p style="color: #b0bec5; margin: 0; font-size: 1rem;">Summary</p>
            <p style="color: #e0f2f1; margin-top: 1rem; font-size: 1.1rem;">{result['summary']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Full analysis (placeholder - will be replaced with actual crew output)
    with st.expander("📊 View Full Analysis", expanded=True):
        st.markdown(f"""
        ## Full Market Intelligence Report: {stock_symbol}
        
        ### 📰 Latest News
        - Company announces strong Q4 results
        - New product launch expected next quarter
        - Positive analyst upgrades from major banks
        
        ### 💰 Financial Metrics
        - Revenue Growth: +15.3% YoY
        - Profit Margin: 22.5%
        - P/E Ratio: 28.4
        - Debt/Equity: 0.45
        
        ### 🔬 Analyst Insights
        The company shows strong fundamentals with consistent revenue growth and healthy margins. 
        Market sentiment is positive with institutional buying increasing over the past quarter.
        
        ### 💼 Expert Recommendation
        **{result['recommendation']}** - Based on comprehensive analysis of financials, market conditions, 
        and growth prospects. Target price suggests {result['change']} upside potential.
        
        **Risk Factors:** Market volatility, sector competition, regulatory changes
        
        ---
        *Generated by StockSense AI • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*
        """)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Download Report",
            f"Stock Analysis: {stock_symbol}\n{result['summary']}",
            file_name=f"stock_analysis_{stock_symbol}_{datetime.now().strftime('%Y%m%d')}.txt",
            use_container_width=True
        )
    with col2:
        if st.button("📊 View Charts", use_container_width=True):
            st.info("Chart integration coming soon!")
    with col3:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.analysis_result = None
            st.session_state.news_status = 'ready'
            st.session_state.data_status = 'ready'
            st.session_state.analyst_status = 'ready'
            st.session_state.expert_status = 'ready'
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #00c853;">
    <p style="font-size: 1rem; font-weight: 700;">💰 StockSense AI • Powered by CrewAI & Finnhub</p>
    <p style="font-size: 0.8rem; color: #b0bec5; margin-top: 0.5rem;">
        Disclaimer: This is for educational purposes. Not financial advice.
    </p>
</div>
""", unsafe_allow_html=True)