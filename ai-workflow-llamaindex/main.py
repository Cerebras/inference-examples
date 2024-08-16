import streamlit as st
from llama_index.core.agent import ReActAgent
from llama_index.llms.groq import Groq
from llama_index.core.tools import FunctionTool
import io
import contextlib
import re

# Start of Streamlit Application
st.title("AlienMath 🧮👽")

# Load secrets
with st.sidebar:
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    api_key = st.text_input("Cerebras API Key:", type="password")

if not api_key:
    st.markdown("""
    ## Welcome to Cerebras x LlamaIndex Demo!

    Hey! We need your help deciphering the alien's math problems we found. We know that "poofing" two numbers means finding the product of both and 3, and "shooping" two numbers means finding the sum of both and 3. Luckily, our trusty chatbot can help us out.

    To get started:
    1. :red[Enter your Cerebras API Key in the sidebar.]
    2. Ask the bot to complete a calculation.
    3. Get the complete opposite of what you asked.

    """)
    st.info("ex: What is 2 shoop 3 poof 1 shoop 4?")
    st.stop()

def poof(a: float, b: float) -> float:
    """Poofs two numbers and returns the product of the two numbers and 3"""
    return a * b * 3

poof_tool = FunctionTool.from_defaults(fn=poof)

def shoop(a: float, b: float) -> float:
    """Shoops two numbers and returns the sum of the two numbers and 3"""
    return a + b + 3

shoop_tool = FunctionTool.from_defaults(fn=shoop)

user = st.text_input("")
st.info("ex: What is 2 shoop 3 poof 1 shoop 4?")

if st.button("Generate output"):
    if user:
        llm = Groq(model="llama3-70b-8192", api_key=api_key)
        agent = ReActAgent.from_tools([poof_tool, shoop_tool], llm=llm, verbose=True, max_iterations=100)

        # Capture the verbose output in a StringIO buffer
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            with st.spinner(text="Generating result..."):
                response = agent.chat(user + " Use a tool to calculate every step.")

        # Get the verbose output
        verbose_output = output_buffer.getvalue()

        # Remove ANSI escape sequences from the verbose output
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        verbose_output = ansi_escape.sub('', verbose_output)

        # Format the verbose output into HTML
        formatted_output = ""
        lines = verbose_output.splitlines()
        for line in lines:
            if line.startswith("> Running step"):
                formatted_output += f"<div style='margin-bottom: 15px;'><p><b>{line}</b></p>"
            elif "Step input:" in line:
                formatted_output += f"<p><b>Step input:</b> {line.replace('Step input:', '').strip()}</p>"
            elif "Thought:" in line:
                formatted_output += f"<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'><b>Thought:</b> {line.replace('Thought:', '').strip()}</div>"
            elif "Action:" in line:
                formatted_output += f"<div style='background-color: #e8f4f8; padding: 10px; border-radius: 5px;'><b>Action:</b> {line.replace('Action:', '').strip()}</div>"
            elif "Action Input:" in line:
                formatted_output += f"<div style='background-color: #f4f8e8; padding: 10px; border-radius: 5px;'><b>Action Input:</b> {line.replace('Action Input:', '').strip()}</div>"
            elif "Observation:" in line:
                formatted_output += f"<div style='background-color: #fff3cd; padding: 10px; border-radius: 5px;'><b>Observation:</b> {line.replace('Observation:', '').strip()}</div>"
            elif "Answer:" in line:
                formatted_output += f"<div style='background-color: #d4edda; padding: 10px; border-radius: 5px;'><b>Answer:</b> {line.replace('Answer:', '').strip()}</div></div>"
            elif line.strip():  # To catch the "Step input: None" cases
                formatted_output += f"<p style='margin-bottom: 15px;'><b>{line}</b></p>"
            else:
                formatted_output += f"{line}<br>"

        # Display results
        st.subheader("Verbose Output (Step-by-Step):")
        st.markdown(f"<div style='padding: 10px;'>{formatted_output}</div>", unsafe_allow_html=True)

        st.subheader("Your result:")
        st.write(response.response)
        
    else:
        st.warning("Please enter a topic.")
