from crewai import Crew, Task, Agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import asyncio
import streamlit as st

# Streamlit UI setup
st.title("Code migrator </>")
st.sidebar.header("Configuration")

# Input fields
java_version = st.sidebar.text_area(
    "/java version", 11
)
uploaded_file = st.sidebar.file_uploader("Upload Java File", type=['java'])
code = uploaded_file.getvalue().decode()
obj = st.sidebar.text_area("Your objective", f"Upgrade this code to java version {java_version}")
temperature = st.sidebar.slider("Creativity Level", 0.0, 1.0, 0.5)


# LLM initialization
def create_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-8b",
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

llm = create_llm()

# Agent definitions
rewriter = Agent(
    role = "Code rewriter",
    goal = "Rewrite code to meet the objective",
    backstory = "Expert in code rewriter",
    llm = llm,
    verbose = True,
    allow_delegation = False,
)

analyst = Agent(
    role="Code analyst",
    goal="Analyze code and provide feedback",
    backstory="Expert in code analysis",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

# Task pipeline
draft_task = Task(
    description=f"Rewrite the {code} to {obj}",
    agent=rewriter,
    expected_output=f"Partially rewritten code to meet the {obj}",
    context=[code],
    output_file="draft.txt",
)

analysis_task = Task(
    description=f"Analyze the {code} and provide feedback {obj}",
    agent=analyst,
    expected_output=f"Analysis of the code with respect to compilation errors",
    context=[code,obj],
    output_file="analysis.txt",
)

final_code_task = Task(
    description=f"Rewrite the code to meet the {obj}",
    agent=rewriter,
    expected_output=f"Fully rewritten code to meet the {obj}",
    context=[analysis_task],
    output_file="final_code.txt",
)

# Crew setup
love_crew = Crew(
    agents=[rewriter, analyst],
    tasks=[analysis_task],
    verbose=1,
)

# Generate button
if st.button("✨ Ugrade code"):
    with st.spinner(" Rewriting your code"):
        try:
            # Execute workflow
            love_crew.kickoff()

            # Get final output
            final_code = analysis_task.output.result

            # Create columns for side-by-side display
            col1, col2 = st.columns([1, 1])

            # Display original code on left side
            with col1:
                st.subheader("Original Code")
                st.code(
                    code,
                    language="java",
                    line_numbers=True
                )

            # Display upgraded code on right side
            with col2:
                st.subheader("Upgraded Code") 
                st.code(
                    final_code,
                    language="java",
                    line_numbers=True
                )            
                # Add download button
            st.download_button(
                label="Download Code",
                data=final_code,
                file_name="upgraded_code.java",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Couldn't upgrade code: {str(e)}")