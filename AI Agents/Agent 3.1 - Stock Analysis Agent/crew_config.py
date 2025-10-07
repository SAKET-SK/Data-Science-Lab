from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM
llm = LLM(
    model = os.getenv("OPENROUTER_MODEL"),  
    temperature=0.4,
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY"),
)

# Define your agents
researcher = Agent(
    role="AI Researcher",
    goal="Analyze emerging AI trends",
    backstory="You are an expert AI analyst who studies AI developments daily. "
              "You provide accurate, well-researched insights.",
    llm=llm,
    verbose=True
)

writer = Agent(
    role="Technical Writer",
    goal="Explain AI trends in simple language",
    backstory="You are a skilled technical writer who excels at making complex "
              "AI concepts accessible to developers and non-technical readers.",
    llm=llm,
    verbose=True
)

# Function to run the crew
def analyze_trend(topic, depth="Standard", audience="Developers", 
                  include_sources=True, include_examples=True):
    """
    Run the AI trends analysis crew
    """
    # Create tasks
    research_task = Task(
        description=f"""Research and analyze emerging AI trends related to: {topic}
        
        Analysis depth: {depth}
        Focus on:
        - Recent developments and breakthroughs
        - Technical accuracy and data points
        - Practical implications for the industry
        - Key players and innovations
        
        Provide comprehensive research findings.""",
        agent=researcher,
        expected_output="Detailed research findings with key trends, data, and analysis"
    )
    
    write_task = Task(
        description=f"""Write a clear, comprehensive analysis about: {topic}
        
        Target audience: {audience}
        Include practical examples: {include_examples}
        Include source references: {include_sources}
        
        Structure the content with:
        - Executive summary
        - Key findings
        - Technical deep dive
        - Business impact
        - Practical examples (if requested)
        - Recommendations
        
        Make it accessible, actionable, and engaging.""",
        agent=writer,
        expected_output="Well-structured article in markdown format"
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    result = crew.kickoff()
    return str(result)