import streamlit as st
import os
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain_cerebras import ChatCerebras
import io
import re
import contextlib

# Add tracing in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Start of Streamlit Application
st.title("A Daily Dose of LLM 📰")

# Load secrets
with st.sidebar:
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    api_key = st.text_input("Cerebras API Key:", type="password")
    st.markdown("### :red[Enter your LangChain API Key below]")
    os.environ["LANGCHAIN_API_KEY"] = st.text_input("LangChain API Key:", type="password")

if not api_key or not os.environ["LANGCHAIN_API_KEY"]:
    st.markdown("""
    ## Welcome to Cerebras x LangChain Agentic Workflow Demo!

    Needed a summary of today's news? You probably headed to Google to search, not your average LLM. This bot is different, however, it can search the internet *for you*! This app implements LangChain's tool-calling agent to interact with Cerebras API. 
                
    To get started:
    1. :red[Enter your Cerebras and LangChain API Keys in the sidebar.]
    2. Ask the bot for something you want the latest update of, such as today's news report.
    3. Lay back, relax, and read a summary of the news.

    """)
    st.info("ex: What is the latest update on the US Presidential Election?")
    st.stop()


user_input = st.text_input("")
st.info("ex: What is the latest update on the US Presidential Election?")

if st.button("Generate output"):
    if user_input:
        # Initialize llm
        llm = ChatCerebras(model="llama3.1-70b", api_key=api_key)
        # Load tools
        tools = load_tools(["ddg-search", "wikipedia"], llm=llm)

        agent = initialize_agent(tools,
                                llm,
                                agent="zero-shot-react-description",
                                verbose=True)

        # Capture the verbose output in a StringIO buffer
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            with st.spinner(text="Generating result..."):
                result = agent.run(
                    user_input
                )

         # Get the verbose output
        verbose_output = output_buffer.getvalue()

        # Remove ANSI escape sequences from the verbose output
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        verbose_output = ansi_escape.sub('', verbose_output)

        # Format the verbose output into HTML
        formatted_output = ""
        lines = verbose_output.splitlines()
        for line in lines:
            if "Thought:" in line:
                formatted_output += f"<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px;'><b>Thought:</b> {line.replace('Thought:', '').strip()}</div>"
            elif "Action:" in line:
                formatted_output += f"<div style='background-color: #e8f4f8; padding: 10px; border-radius: 5px;'><b>Action:</b> {line.replace('Action:', '').strip()}</div>"
            elif "Action Input:" in line:
                formatted_output += f"<div style='background-color: #f4f8e8; padding: 10px; border-radius: 5px;'><b>Action Input:</b> {line.replace('Action Input:', '').strip()}</div>"
            elif "Observation:" in line:
                formatted_output += f"<div style='background-color: #fff3cd; padding: 10px; border-radius: 5px;'><b>Observation:</b> {line.replace('Observation:', '').strip()}</div>"
            elif "Final Answer:" in line:
                formatted_output += f"<div style='background-color: #d4edda; padding: 10px; border-radius: 5px;'><b>Answer:</b> {line.replace('Answer:', '').strip()}</div></div>"

        # Display results
        st.subheader("Verbose Output (Step-by-Step):")
        st.markdown(f"<div style='padding: 10px;'>{formatted_output}</div>", unsafe_allow_html=True)

        st.subheader("Your result:")
        st.write(result)
        
    else:
        st.warning("Please enter a topic.")