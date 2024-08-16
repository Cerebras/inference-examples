## Agentic Workflows for a Fifth Grader: An example with LangChain

This tutorial outlines the setup, code structure, and the implementation of a simple agentic workflow using Cerebras and LangChain.

<!-- ![finished product](./alienMath.png) -->

### Step 1: Set up your API Keys

1. **Obtain Your API Keys**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key. Log in to your [LangChain account](https://smith.langchain.com) and click on the settings cog in the bottom left corner to generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras and LangChain API keys, add them to the sidebar on the left.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API. Use the following command to install the library along with other dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Start your App

Run the command `streamlit run main.py` to start up the frontend.

---

https://python.langchain.com/v0.1/docs/use_cases/tool_use/quickstart/#agents