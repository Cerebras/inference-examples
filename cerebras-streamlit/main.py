import streamlit as st
from cerebras.cloud.sdk import Cerebras
import webbrowser

repl_link = "https://replit.com/@EmilyChen10/AI-Agentic-Workflow-Example-with-LlamaIndex-V2#main.py"

st.set_page_config(page_icon="🤖", layout="wide",
       page_title="Cerebras")

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

icon("🧠")
st.title("Cerebras")
st.subheader("Deploying Cerebras on Streamlit", divider="orange", anchor=False)

with st.sidebar:
    if st.button('Spin up your own on Repl.it :material/code:', type='secondary'):
        webbrowser.open(repl_link)
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    api_key = st.text_input("Cerebras API Key:", type="password")

if not api_key:
    st.markdown("""
    ## Welcome to Cerebras x Streamlit Demo!

    This simple chatbot app was created just for you to demonstrate how you can use Cerebras with Streamlit.

    To get started:
    1. :red[Enter your Cerebras API Key in the sidebar.]
    2. Chat away, powered by Cerebras.

    """)
    st.stop()
    
# Create the Cerebras client
client = Cerebras(
    # This is the default and can be omitted
    api_key=api_key,
)

# Initialize chat history and selected model
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# Define model details
models = {
    "llama3.1-8b": {"name": "Llama3.1-8b", "tokens": 8192, "developer": "Meta"}, 
    "llama3.1-70b": {"name": "Llama3.1-70b", "tokens": 8192, "developer": "Meta"}
}

# Layout for model selection and max_tokens slider
col1, col2 = st.columns(2)

with col1:
    model_option = st.selectbox(
        "Choose a model:",
        options=list(models.keys()),
        format_func=lambda x: models[x]["name"]    
    )

# Detect model change and clear chat history if model has changed
if st.session_state.selected_model != model_option:
    st.session_state.messages = []
    st.session_state.selected_model = model_option

max_tokens_range = models[model_option]["tokens"]

with col2:
    # Adjust max_tokens slider based on the selected model
    max_tokens = st.slider(
        "Max Tokens:",
        min_value=512,
        max_value=max_tokens_range,
        value=max_tokens_range,
        step=512,
        help=f"Select the maximum number of tokens (words) for the model's response."
    )

# Display chat messages stored in history on app rerun
for message in st.session_state.messages:
    avatar = '🤖' if message["role"] == "assistant" else '🦔'
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your prompt here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar='🦔'):
        st.markdown(prompt)

    # Fetch response from Cerebras API
    try:
        chat_completion = client.chat.completions.create(
            model=model_option,
            messages=[
                {"role": "user", 
                 "content": prompt}
            ],
            max_tokens=max_tokens
        )

        # Display response from Cerebras API
        with st.chat_message("assistant", avatar="🤖"):
            response = chat_completion.choices[0].message.content
            # Save response to chat history
            st.session_state.messages.append(
                {"role": "assistant", "content": response})
            st.markdown(response)
    except Exception as e:
        st.error(e, icon="🚨")