import streamlit as st
import os
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_cerebras import ChatCerebras
from langchain_core.tools import tool

# Add tracing in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Start of Streamlit Application
st.title("A Fifth-Grader's Best Friend 👦🏽")

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

    Do you hate math word problems? We taught this bot to do the math homework of the fifth grader in your life with our custom functions. This app implements LangChain's tool-calling agent to interact with Cerebras API. 
                
    To get started:
    1. :red[Enter your Cerebras and LangChain API Keys in the sidebar.]
    2. Ask the bot to complete a calculation.
    3. Let the bot do your fifth grader's homework for you.

    """)
    st.info("ex: Take 3 to the fifth power and multiply that by the sum of twelve and three, then square the whole result!")
    st.stop()

# Get the prompt to use - can be replaced with any prompt that includes variables "agent_scratchpad" and "input"!
prompt = hub.pull("hwchase17/openai-tools-agent")

@tool
def multiply(first_int: int, second_int: int) -> int:
    """Multiply two integers together."""
    return first_int * second_int

@tool
def add(first_int: int, second_int: int) -> int:
    """Add two integers."""
    return first_int + second_int

@tool
def exponentiate(base: int, exponent: int) -> int:
    """Exponentiate the base to the exponent power."""
    return base**exponent

tools = [multiply, add, exponentiate]

user = st.text_input("")
st.info("ex: Take 3 to the fifth power and multiply that by the sum of twelve and three, then square the whole result!")

if st.button("Generate output"):
    if user:
        llm = ChatCerebras(model="llama3.1-70b", api_key=api_key)

        # Construct the tool calling agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        # Create an agent executor by passing in the agent and tools
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        with st.spinner(text="Generating result..."):
            result = agent_executor.invoke(
                {
                    "input": user
                }
            )
        # Display results
        st.subheader("Your result:")
        st.write(result["output"])
        
    else:
        st.warning("Please enter a topic.")