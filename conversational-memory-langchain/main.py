import streamlit as st
import webbrowser

from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

# Importing dependencies for custom LLM implementation
from cerebras.cloud.sdk import Cerebras
from typing import Any, List, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM

class CerebrasLLM(LLM):
    """A custom LLM implementation for the Cerebras API."""

    api_key: str
    model_name: str

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")

        # Create a completion request to the Cerebras API
        user_message = {"role": "user", "content": prompt}
        response = Cerebras(api_key=self.api_key).chat.completions.create(
            messages=[user_message],
            model=self.model_name,
            **kwargs
        )

        # Calculate tokens per second
        total_tokens = response.usage.total_tokens
        total_time = response.time_info.total_time
        tokens_per_second = total_tokens / total_time

        # Extract and return the text from the response along with metric
        return response.choices[0].message.content + f"\n(Tokens per second: {tokens_per_second:.2f})"

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model. Used for logging purposes only."""
        return "cerebras"

def main():
    """
    This is the main entry point of the application. It initializes our custom LLM object and handles interaction with the user.
    """
    
    repl_link = "https://replit.com/@EmilyChen10/Chatbot-with-Conversational-Memory-on-LangChain#main.py"
    
    st.title("HyperthymesiaBot")

    with st.sidebar:
        if st.button('Spin up your own on Repl.it :material/code:', type='secondary'):
            webbrowser.open(repl_link)
        st.title("Settings")
        st.markdown("### :red[Enter your Cerebras API Key below]")
        api_key = st.text_input("Cerebras API Key:", type="password")

    models = ["llama3.1-8b", "llama3.1-70b"]
    system_prompt = 'You are a friendly conversational chatbot'
    conversational_memory_length = 5 # number of previous messages the chatbot will remember during the conversation

    if not api_key:
        st.markdown("""
        ## Welcome to Cerebras x LangChain Demo!
    
        This simple chatbot app can remember up to 5 previous messages (it has conversational memory!) and uses the Cerebras API to generate responses.
    
        To get started:
        1. :red[Enter your Cerebras API Key in the sidebar.]
        2. Choose a model you want to test out.
        3. Chat with the HyperthymesiaBot!

        """)
        # st.image("https://via.placeholder.com/600x300.png?text=Fast+Adaptive+Quiz", use_column_width=True)
        # st.info("Conversational Memory with LangChain")
        st.stop()

    model_option = st.selectbox(
        "Choose a model:",
        options=models
    )

    # Initialize history and chatbot memory
    if 'history' not in st.session_state:
        st.session_state.history = []

    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # Detect model change and clear chat history if model has changed
    if st.session_state.selected_model != model_option:
        st.session_state.history = []
        st.session_state.memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history", return_messages=True)
        st.session_state.selected_model = model_option

    # Initialize the Cerebras LLM object
    cerebras_llm = CerebrasLLM(api_key=api_key, model_name=st.session_state.selected_model)

    user_input = st.text_input("Let's talk:", "")

    if st.button("Send"):
        # If the user has asked a question,
        if user_input:
            # Construct a chat prompt template using various components
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=system_prompt
                    ),  # This is the persistent system prompt that is always included at the start of the chat.

                    MessagesPlaceholder(
                        variable_name="chat_history"
                    ),  # This placeholder will be replaced by the actual chat history during the conversation. It helps in maintaining context.

                    HumanMessagePromptTemplate.from_template(
                        "{human_input}"
                    ),  # This template is where the user's current input will be injected into the prompt.
                ]
            )

            # Create a conversation chain using the LangChain LLM (Language Learning Model)
            conversation = LLMChain(
                llm=cerebras_llm,  # The Groq LangChain chat object initialized earlier.
                prompt=prompt,  # The constructed prompt template.
                verbose=False,   # TRUE Enables verbose output, which can be useful for debugging.
                memory=st.session_state.memory,  # The conversational memory object that stores and manages the conversation history.
            )
            # The chatbot's answer is generated by sending the full prompt to the Groq API.
            response = conversation.predict(human_input=user_input)

            # Append the user's input and the chatbot's response to the conversation history
            st.session_state.history.append(f"User: {user_input}")
            st.session_state.history.append(f"Chatbot: {response}")
            
    # Display the chat history
    if st.session_state.history:
        st.write("### Conversation History:")
        for message in st.session_state.history:
            st.write(message)

if __name__ == "__main__":
    main()