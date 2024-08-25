## Agentic Workflows for Daily Use: An example with LangChain

This tutorial outlines the setup, code structure, and the implementation of a simple agentic workflow using Cerebras and LangChain.

<!-- ![finished product](./alienMath.png) -->

### Step 1: Set up your API Keys

1. **Obtain Your API Keys**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key. Log in to your [LangChain account](https://smith.langchain.com) and click on the settings cog in the bottom left corner to generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras and LangChain API keys, add them to the sidebar on the left.

### Step 2: Install dependencies

Let's make sure we have all of the requirements for this project installed!
```bash
pip install -r requirements.txt
```

### Step 3: What's hot off the press?

Run the command `streamlit run main.py` to start up the frontend.

### What is an agentic workflow?
Within the context of LangChain, an agent is a software component driven by a large language model (LLM). It's assigned a task performs a sequence of actions to achieve it.

An "tool calling agent" in LangChain uses a set of tools to evaluate this task. **In this example, we'll be using tools `wikipedia` and `ddg-search` (DuckDuckGo) to retrieve real-time information from the internet.**

The agent evaluates these tools to determine the most effective one for each step. Once a step is completed, the agent assesses whether the task is finished and, if so, delivers the result to the user. If the task is not yet complete, the agent returns to the beginning of the process to continue with the next step. **You can see this workflow in action from the output of your request.**

### Code Overview

#### 1. Define Basic Tools

Before we do anything, we must load our LLM as well as the tools it will use from LangChain. You can take a look at the other available native tools [here](https://github.com/langchain-ai/langchain/blob/ccb9e3ee2d4ffde1bb33c6c0df0db87aff3341bf/libs/langchain/langchain/agents/load_tools.py#L409).

```python
from langchain.agents import load_tools
from langchain_cerebras import ChatCerebras

# Initialize llm
llm = ChatCerebras(model="llama3.1-70b", api_key=api_key)
# Load tools
tools = load_tools(["ddg-search", "wikipedia"], llm=llm)
```

### 2. Processing User Input and Creating the Agent

The application collects user input for the prompt:

```python
user = st.text_input("")
st.info("ex: What is the latest update on the US Presidential Election?")
```

`initialize_agent` is a handy function from LangChain that allows us to easily create an agent. If you're curious about the prompt that the agent uses to interact with the LLM, try printing it out: `print(agent.agent.llm_chain.prompt.template)`

```python
from langchain.agents import initialize_agent

agent = initialize_agent(tools,
                        llm,
                        agent="zero-shot-react-description",
                        verbose=True)
```

#### 3. Capturing Output

By running the `agent`, we can then call the agent with the user's query. The agentic workflow is begun, and the process will continue until the entire query is evaluated.

```python
# Capture the verbose output in a StringIO buffer
output_buffer = io.StringIO()
with contextlib.redirect_stdout(output_buffer):
    with st.spinner(text="Generating result..."):
        result = agent.run(
            user_input
        )
```

Read more about custom agents in [LangChain's blog](https://python.langchain.com/v0.1/docs/use_cases/tool_use/quickstart/#agents).