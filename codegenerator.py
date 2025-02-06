from crewai import Crew, Task, Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.llms import Ollama
import os
import asyncio
import streamlit as st

class CodeMigrator:
    def __init__(self):
        self.setup_streamlit()
        self.llm = self.create_llm()
        self.setup_agents()
        self.setup_tasks()
        self.setup_crew()

    def setup_streamlit(self):
        st.set_page_config(layout="wide")
        st.title("Code migrator </>")
        st.sidebar.header("Configuration")

        st.markdown("""
            <style>
            body, html {
                overflow: hidden;
            }
            </style>
            """, unsafe_allow_html=True)

        self.java_version = st.sidebar.text_area("/java version", "")
        self.uploaded_file = st.sidebar.file_uploader("Upload File", type=['java', 'xml'])    
        if self.uploaded_file is not None:
            self.code = self.uploaded_file.getvalue().decode()
        else:
            self.code = ""
        self.obj = st.sidebar.text_area("Your objective", f"Upgrade this code to java version {self.java_version}")
        self.temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)

    def create_llm(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        #return ChatGoogleGenerativeAI(
        #     # model="gemini-1.5-flash-8b",
        #     # temperature=self.temperature,
        #     # google_api_key=os.getenv("GOOGLE_API_KEY"),
            
        # )
        return Ollama(
                model="deepseek-r1:1.5b"
            
        )
    def setup_agents(self):
        self.rewriter = Agent(
            role="Code rewriter",
            goal=f"Rewrite full code to meet the objective {self.java_version} {self.code} {self.obj}",
            backstory=f"Expert in code rewriter {self.java_version} {self.code} {self.obj}",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        self.analyst = Agent(
            role="Code analyst", 
            goal=f"Analyze code and provide feedback {self.java_version} {self.code} {self.obj}",
            backstory=f"Expert in code analysis {self.java_version} {self.code} {self.obj}",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def setup_tasks(self):
        # We only need two tasks:
        # 1. Analysis task to understand the code and identify needed changes
        # 2. Final code task to implement the changes based on analysis
        self.analysis_task = Task(
            description=f"Analyze the {self.code} {self.obj}",
            agent=self.analyst,
            expected_output=f"Analysis of the code with respect to compilation errors",
            context=[self.code, self.obj],
            output_file="analysis.txt",
        )

        self.final_code_task = Task(
            description=f"Rewrite the full code to meet the {self.code} {self.obj}",
            agent=self.rewriter,
            expected_output=f"Fully rewritten code to meet the {self.code} {self.obj}",
            context=[self.analysis_task],
            output_file="final_code.txt",
        )

    def setup_crew(self):
        self.code_crew = Crew(
            agents=[self.rewriter, self.analyst],
            tasks=[self.analysis_task, self.final_code_task],
            verbose=1,
        )

    def display_code(self, final_code):
        col1, col2 = st.columns([4, 4])
        
        with col1:
            st.subheader("Original Code")
            with st.container():
                st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                st.code(
                    self.code,
                    language="java",
                    line_numbers=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.subheader("Upgraded Code")
            with st.container():
                st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
                st.code(
                    final_code,
                    language="java",
                    line_numbers=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="Download Code",
            data=final_code,
            file_name="upgraded_code.java",
            mime="text/plain"
        )

    def run(self):
        if st.button("✨ Ugrade code"):
            with st.spinner(" Rewriting your code"):
                try:
                    self.code_crew.kickoff()
                    final_code = self.final_code_task.output.result
                    self.display_code(final_code)
                except Exception as e:
                    st.error(f"Couldn't upgrade code: {str(e)}")

if __name__ == "__main__":
    migrator = CodeMigrator()
    migrator.run()
# # Streamlit UI setup
# st.set_page_config( layout="wide")
# st.title("Code migrator </>")
# st.sidebar.header("Configuration")

# st.markdown("""
#     <style>
#     body, html {
#         overflow: hidden;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # Input fields
# java_version = st.sidebar.text_area(
#     "/java version",""
# )
# uploaded_file = st.sidebar.file_uploader("Upload Java File", type=['java'])
# if uploaded_file is not None:
#     code = uploaded_file.getvalue().decode()
# else:
#     code = ""
# obj = st.sidebar.text_area("Your objective", f"Upgrade this code to java version {java_version}")
# temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.5)

# # LLM initialization
# def create_llm():
#     return ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash-8b",
#         temperature=temperature,
#         google_api_key=os.getenv("GOOGLE_API_KEY"),
#     )


# try:
#     loop = asyncio.get_event_loop()
# except RuntimeError:
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)

# llm = create_llm()

# # Agent definitions
# rewriter = Agent(
#     role = "Code rewriter",
#     goal = "Rewrite code to meet the objective",
#     backstory = "Expert in code rewriter",
#     llm = llm,
#     verbose = True,
#     allow_delegation = False,
# )

# analyst = Agent(
#     role="Code analyst",
#     goal="Analyze code and provide feedback",
#     backstory="Expert in code analysis",
#     llm=llm,
#     verbose=True,
#     allow_delegation=False,
# )

# # Task pipeline
# draft_task = Task(
#     description=f"Rewrite the {code} to {obj}",
#     agent=rewriter,
#     expected_output=f"Partially rewritten code to meet the {obj}",
#     context=[code],
#     output_file="draft.txt",
# )

# analysis_task = Task(
#     description=f"Analyze the {code} and provide feedback {obj}",
#     agent=analyst,
#     expected_output=f"Analysis of the code with respect to compilation errors",
#     context=[code,obj],
#     output_file="analysis.txt",
# )

# final_code_task = Task(
#     description=f"Rewrite the code to meet the {obj}",
#     agent=rewriter,
#     expected_output=f"Fully rewritten code to meet the {obj}",
#     context=[analysis_task],
#     output_file="final_code.txt",
# )

# # Crew setup
# code_crew = Crew(
#     agents=[rewriter, analyst],
#     tasks=[analysis_task],
#     verbose=1,
# )

# # Generate button
# if st.button("✨ Ugrade code"):

#     with st.spinner(" Rewriting your code"):
#         try:
#             # Execute workflow
#             code_crew.kickoff()

#             # Get final output
#             final_code = analysis_task.output.result

            
#             # Create columns for side-by-side display
#             col1, col2 = st.columns([4, 4])
            
#             # Display original code on left side
#             with col1:
                
#                 st.subheader("Original Code")
#                 with st.container():
#                     st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
#                     st.code(
#                         code,
#                         language="java",
#                         line_numbers=True
#                     )
#                     st.markdown('</div>', unsafe_allow_html=True)

#             # Display upgraded code on right side
#             with col2:
#                 st.subheader("Upgraded Code") 
#                 with st.container():
#                     st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
#                     st.code(
#                         final_code,
#                         language="java",  
#                         line_numbers=True
#                     )       
#                     st.markdown('</div>', unsafe_allow_html=True)     
#                 # Add download button
#             st.download_button(
#                 label="Download Code",
#                 data=final_code,
#                 file_name="upgraded_code.java",
#                 mime="text/plain"
#             )

#         except Exception as e:
#             st.error(f"Couldn't upgrade code: {str(e)}")
