import os
import streamlit as st
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import END
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI

# Add tracing in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Start of Streamlit Application
st.title("A Three Person Job: Blog Writing with Multi Agentic Workflow ✏️")

# Load secrets
with st.sidebar:
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    api_key = st.text_input("Cerebras API Key:", type="password")
    st.markdown("### :red[Enter your Tavily API Key below]")
    os.environ["TAVILY_API_KEY"] = st.text_input("Tavily API Key:", type="password")
    st.markdown("### :red[Enter your LangChain API Key below]")
    os.environ["LANGCHAIN_API_KEY"] = st.text_input("LangChain API Key:", type="password")

if not api_key or not os.environ.get("TAVILY_API_KEY") or not os.environ.get("LANGCHAIN_API_KEY"):
    st.markdown("""
    ## Welcome to Cerebras x LangChain & LangGraph Agentic Workflow Demo!

    A researcher, editor, and writer walk into a bar. Except, this bar is an agentic workflow. This demo showcases a multi-agent workflow for generating a blog post based on a query.
                
    To get started:
    1. :red[Enter your Cerebras and Tavily API Keys in the sidebar.]
    2. Ask the bot to write a blog about a topic.
    3. The bot will search for information, evaluate it, and write a blog post.

    """)
    st.info("ex: What are the differences between LangChain and LangGraph?")
    st.stop()

class State(TypedDict):
    query: Annotated[list, add_messages]
    research: Annotated[list, add_messages]
    content: str
    content_ready: bool
    iteration_count: int  # Counter for iterations

# Initialize the StateGraph
graph = StateGraph(State)

# Initialize ChatOpenAI instance for language model
llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0)


class ResearchAgent:
    def __init__(self):
        pass
    
    def format_search(self, query: str) -> str:
        # Prepare prompt for the language model to optimize the search query
        # Using Few-Shot Prompting to ensure we receive only the optimized query
        prompt = (
            "You are an expert at optimizing search queries for Google. "
            "Your task is to take a given query and return an optimized version of it, making it more likely to yield relevant results. "
            "Do not include any explanations or extra text, only the optimized query.\n\n"
            "Example:\n"
            "Original: best laptop 2023 for programming\n"
            "Optimized: top laptops 2023 for coding\n\n"
            "Example:\n"
            "Original: how to train a puppy not to bite\n"
            "Optimized: puppy training tips to prevent biting\n\n"
            "Now optimize the following query:\n"
            f"Original: {query}\n"
            "Optimized:"
        )
        
        # Invoke language model to optimize query
        response = llm.invoke(prompt)
        return response.content
    
    def search(self, state: State):
        # Initialize TavilySearchResults instance to perform the web search
        search = TavilySearchResults(max_results=1)
        # Get the latest query from the state and optimize it using the format_search method
        optimized_query = self.format_search(state.get('query', "")[-1].content)
        # Perform the search using the optimized query
        results = search.invoke(optimized_query)
        # Return only the content from the research results
        return {"research": [results[0]["content"]]}
    
class EditorAgent:
    def __init__(self):
        pass
    
    def evaluate_research(self, state: State):
        # Combine all queries into a single string
        query = '\n'.join(message.content for message in state.get("query"))
        print(f"Query/queries: {query}")
        print("-"*20)
        
        # Combine all research content into a single string
        research = '\n'.join(message.content for message in state.get("research"))
        print(f"Research Content: {research}")
        print("-"*20)
        
        # Get the current iteration count, defaulting to 1 if not set
        iteration_count = state.get("iteration_count", 1)
        
        # Ensure iteration_count is always an integer
        if iteration_count is None:
            iteration_count = 1
        
        print(f"Iteration n.: {iteration_count}")
        print("-"*20)
        
        # Limit to 3 iterations to avoid infinite loops
        if iteration_count >= 3:
            return {"content_ready": True}
        
        # Prepare the prompt for the language model to evaluate the research
        prompt = (
            "You are an expert editor. Your task is to evaluate the research based on the query. "
            "If the information is sufficient to create a comprehensive and accurate blog post, respond with 'sufficient'. "
            "If the information is not sufficient, respond with 'insufficient' and provide a new, creative query suggestion to improve the results. "
            "If the research results appear repetitive or not diverse enough, think about a very different kind of question that could yield more varied and relevant information. "
            "Consider the depth, relevance, and completeness of the information when making your decision.\n\n"
            "Example 1:\n"
            "Used queries: What are the benefits of a Mediterranean diet?\n"
            "Research: The Mediterranean diet includes fruits, vegetables, whole grains, and healthy fats.\n"
            "Evaluation: Insufficient\n"
            "New query: Detailed health benefits of a Mediterranean diet\n\n"
            "Example 2:\n"
            "Used queries: How does solar power work?\n"
            "Research: Solar power works by converting sunlight into electricity using photovoltaic cells.\n"
            "Evaluation: Sufficient\n\n"
            "Example 3:\n"
            "Used queries: Effects of climate change on polar bears?\n"
            "Research: Climate change is reducing sea ice, affecting polar bear habitats.\n"
            "Evaluation: Insufficient\n"
            "New query: How are polar bears adapting to the loss of sea ice due to climate change?\n\n"
            "Now evaluate the following:\n"
            f"Used queries: {query}\n"
            f"Research: {research}\n\n"
            "Evaluation (sufficient/insufficient):\n"
            "New query (if insufficient):"
        )
        
        # Invoke the language model with the prompt
        response = llm.invoke(prompt)
        evaluation = response.content.strip()
        
        # Display the evaluation result for debugging purposes
        print(f"Eval: {evaluation}")
        print("-"*20)
        
        # Check if a new query is suggested in the evaluation
        if "new query:" in evaluation.lower():
            new_query = evaluation.split("New query:", 1)[-1].strip()
            return {"query": [new_query], "iteration_count": iteration_count + 1}
        else:
            return {"content_ready": True}
        
class WriterAgent:
    def __init__(self):
        pass
    
    def write_blogpost(self, state: State):
        # Extract the original query from the state
        query = state.get("query")[0].content
        # Combine all research content into a single string
        research = '\n'.join(message.content for message in state.get("research"))
        
        # Prepare the prompt for the language model to write the blog post
        prompt = (
            "You are an expert blog post writer. Your task is to take a given query and context, and write a comprehensive, engaging, and informative short blog post about it. "
            "Make sure to include an introduction, main body with detailed information, and a conclusion. Use a friendly and accessible tone, and ensure the content is well-structured and easy to read.\n\n"
            f"Query: {query}\n\n"
            f"Context:\n{research}\n\n"
            "Write a detailed and engaging blog post based on the above query and context."
        )
        
        # Invoke the language model with the prompt to generate the blog post
        response = llm.invoke(prompt)
        
        # Return the generated content
        return {"content": response.content}

# Define nodes: Adding each agent to the graph as a node
# "search_agent" uses the search method of the ResearchAgent
# "writer_agent" uses the write_blogpost method of the WriterAgent
# "editor_agent" uses the evaluate_research method of the EditorAgent
graph.add_node("search_agent", ResearchAgent().search)
graph.add_node("writer_agent", WriterAgent().write_blogpost)
graph.add_node("editor_agent", EditorAgent().evaluate_research)

# Set entry point: The graph starts with the search_agent node
graph.set_entry_point("search_agent")

# Define edges: Connect the nodes in the order they should be executed
# After search_agent finishes, editor_agent is triggered
graph.add_edge("search_agent", "editor_agent")

# Define conditional edges for the editor agent
# Depending on the evaluation result, either proceed to writer_agent or go back to search_agent for revision
graph.add_conditional_edges(
    "editor_agent",
    lambda state: "accept" if state.get("content_ready") else "revise",
    {
        "accept": "writer_agent", # If content is ready, proceed to writer_agent
        "revise": "search_agent" # If content is not ready, go back to search_agent
    }
)

# Define edge to end the graph once the writer_agent is done
graph.add_edge("writer_agent", END)

# Compile the graph to finalize its structure
graph = graph.compile()

user_input = st.text_input("")
st.info("ex: What are the differences between LangChain and LangGraph?")

if st.button("Generate output"):
    if user_input:
        with st.spinner("Generating blog post..."):
            blogpost = graph.invoke({"query": user_input})
        st.write(blogpost["content"])