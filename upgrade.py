
import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain_community.llms import Ollama
import zipfile
import xml.etree.ElementTree as ET
import os
import re
import difflib

# Initialize LLM
def create_llm():
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # return ChatGoogleGenerativeAI(
    #     model="gemini-1.5-flash-8b", 
    #     temperature=0.7,
    #     google_api_key=os.getenv("GOOGLE_API_KEY"),
    # )
    return Ollama(model="deepseek-coder-v2:16b")

llm = create_llm()
# Create agents
file_analyzer = Agent(
    role='File Analyzer',
    goal='Analyze zip file contents and extract pom.xml and java files',
    backstory='Expert at analyzing Java project structures and dependencies',
    llm=llm,
    tools=[
        Tool(
            name='analyze_zip',
            func=lambda x: zipfile.ZipFile(x).namelist(),
            description='Analyzes contents of zip file'
        )
    ]
)

pom_updater = Agent(
    role='POM Updater', 
    goal='Update Java version in pom.xml files and upgrade java code if needed',
    backstory='Expert at modifying Maven configuration files and Java code',
    llm=llm,
    tools=[
        Tool(
            name='update_pom',
            func=lambda x,y: ET.parse(x).find(".//java.version").text,
            description='Updates Java version in pom.xml'
        )
    ]
)

def update_java_file(file_path, new_version):
    # Store original content
    with open(file_path, 'r') as file:
        original_content = file.read()
    
    content = original_content
    
    # Check for Java version-specific syntax changes needed
    changes_made = False
    
    # Example: Update var keyword usage (Java 10+)
    if int(new_version) >= 10:
        var_pattern = r'(final\s+)?(\w+)\s+(\w+)(\s*=\s*new\s+\w+.*?;)'
        content = re.sub(var_pattern, lambda m: f"{m.group(1) or ''}var {m.group(3)}{m.group(4)}", content)
        if content != original_content:
            changes_made = True
            
    # Example: Update switch expressions (Java 14+)
    if int(new_version) >= 14:
        # Simple switch expression update
        switch_pattern = r'switch\s*\((.*?)\)\s*\{(.*?)\}'
        content = re.sub(switch_pattern, lambda m: update_switch_syntax(m.group(1), m.group(2)), content)
        if content != original_content:
            changes_made = True
    
    # Generate diff if changes were made
    if changes_made:
        diff = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f'Original {os.path.basename(file_path)}',
            tofile=f'Updated {os.path.basename(file_path)}'
        ))
        
        # Write updated content
        with open(file_path, 'w') as file:
            file.write(content)
            
        return file_path, ''.join(diff)
    
    return file_path, ''

def update_switch_syntax(condition, body):
    # Simple switch expression transformation
    # This is a basic example - real implementation would need more sophisticated parsing
    return f'switch ({condition}) {{\n{body}\n}}'

def process_zip_file(uploaded_file, new_java_version):
    # Extract zip contents
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall("temp")
        
    # Find pom.xml and java files
    pom_path = None
    java_files = []
    modified_files = []
    file_diffs = {}
    
    for root, dirs, files in os.walk("temp"):
        if "pom.xml" in files:
            pom_path = os.path.join(root, "pom.xml")
            modified_files.append(pom_path)
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))
            
    if pom_path:
        # Store original pom content
        with open(pom_path, 'r') as f:
            original_pom = f.read()
            
        # Update pom.xml
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # Find and update Java version
        for prop in root.findall(".//{*}properties/{*}java.version"):
            prop.text = new_java_version
            
        tree.write(pom_path)
        
        # Generate pom.xml diff
        with open(pom_path, 'r') as f:
            updated_pom = f.read()
        pom_diff = list(difflib.unified_diff(
            original_pom.splitlines(keepends=True),
            updated_pom.splitlines(keepends=True),
            fromfile='Original pom.xml',
            tofile='Updated pom.xml'
        ))
        file_diffs[pom_path] = ''.join(pom_diff)
        
        # Update Java files
        for java_file in java_files:
            modified_file, diff = update_java_file(java_file, new_java_version)
            modified_files.append(modified_file)
            file_diffs[modified_file] = diff
        
        # Create new zip
        new_zip_name = "updated_" + uploaded_file.name
        with zipfile.ZipFile(new_zip_name, 'w') as new_zip:
            for root, dirs, files in os.walk("temp"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "temp")
                    new_zip.write(file_path, arcname)
                    
        return new_zip_name, modified_files, file_diffs
    
    return None, [], {}

# Streamlit UI
st.title("Java Project Version Updater")

uploaded_file = st.file_uploader("Upload ZIP file", type="zip")
new_version = st.text_input("New Java Version", "17")

if uploaded_file and new_version:
    if st.button("Process"):
        with st.spinner("Processing..."):
            # Create crew and execute tasks
            crew = Crew(
                agents=[file_analyzer, pom_updater],
                tasks=[
                    Task(
                        description=f"Analyze zip file {uploaded_file.name}",
                        agent=file_analyzer
                    ),
                    Task(
                        description=f"Update Java version to {new_version}",
                        agent=pom_updater
                    )
                ],
                process=Process.sequential
            )
            
            # Process the file
            new_zip, modified_files, file_diffs = process_zip_file(uploaded_file, new_version)
            
            if new_zip:
                st.success(f"Successfully updated Java version to {new_version}")
                
                # Display modified files with diffs
                st.subheader("Modified Files:")
                for file in modified_files:
                    rel_path = os.path.relpath(file, "temp")
                    with st.expander(f"**{rel_path}**"):
                        if file_diffs[file]:
                            st.code(file_diffs[file], language='diff')
                        else:
                            st.text("No changes made to this file")
                
                # Provide download link
                with open(new_zip, "rb") as f:
                    st.download_button(
                        label="Download updated project",
                        data=f,
                        file_name=new_zip,
                        mime="application/zip"
                    )
            else:
                st.error("Could not find pom.xml in the uploaded file")
