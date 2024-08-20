## Streamlining App UI: Streamlit & Cerebras

Streamlit is a simple way to deploy machine learning and other data science applications, with many built-in components ready for customization. This tutorial showcases some of Streamlit's features as integrated with the Cerebras API.

### Step 1: Set up your API Key

1. **Obtain Your API Key**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras API key, add it to the sidebar on the left.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API by using repl's built in `Shell`. Use the following command to install the library:

```bash
pip install https://cerebras-cloud-sdk.s3.us-west-1.amazonaws.com/test/cerebras_cloud_sdk-0.5.0-py3-none-any.whl
```

Go ahead and also run `pip install -r requirements.txt` to install other requirements as well!

### Step 3: Streamline your Streamlit Experience 
Press RUN and then run the command `streamlit run main.py` in Shell to interact with the UI.

### Code Overview

#### **Custom Button**

```python
import streamlit as st
from cerebras.cloud.sdk import Cerebras
import webbrowser

# Repl Button
st.markdown("""
<style>.element-container:has(#button-after) + div button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;     
    }</style>""", unsafe_allow_html=True)

# Button with custom CSS class
st.markdown('<span id="button-after"></span>', unsafe_allow_html=True)
if st.button('Spin up your own on Repl.it :material/code:', type='primary'):
    webbrowser.open(repl_link)
```
- `st.markdown`: Used to add markdown text to the webpage. In this case, it is used to create custom CSS components and styling to generate a button that floats on the bottom right corner of the screen.
- `st.button`: Creates a button, in this case, to open a link.

#### **Page Configuration and Icon**

```python
st.set_page_config(page_icon="🤖", layout="wide",
       page_title="CerebrasLite")

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
        unsafe_allow_html=True,
    )

icon("🧠")
st.title("CerebrasLite")
st.subheader("Deploying Cerebras on Streamlit", divider="orange", anchor=False)
```

- `st.set_page_config`: Configures the layout and icon for the Streamlit app. This method sets the page title and icon, making the app visually appealing and giving it a personalized touch.
- `icon`: A custom function to display an emoji as a large icon. This demonstrates how Streamlit allows for custom HTML styling within the app using the `unsafe_allow_html` parameter.
- `st.title` and `st.subheader`: Used to create a title and a subheader for the app, showcasing how Streamlit handles text elements and layout organization.

#### **Sidebar for API Key Input**

```python
with st.sidebar:
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
```

- `st.sidebar`: Creates a sidebar layout, which is useful for settings or inputs that are not part of the main content area.
- `st.text_input`: Allows users to input their Cerebras API Key securely. The `type="password"` option hides the input text for security.
- `st.markdown`: Displays instructions and a welcome message in Markdown format, providing user guidance on how to start using the app.
- `st.stop()`: Stops further execution if the API key is not provided, ensuring that the app does not run without necessary credentials.

#### **Client Initialization and Session State Management**

```python
client = Cerebras(
    # This is the default and can be omitted
    api_key=api_key,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
```

- `Cerebras`: Initializes the Cerebras client with the API key provided by the user.
- `st.session_state`: Manages state across user interactions, maintaining chat history and selected model state. This demonstrates how Streamlit can persist data between reruns of the app, which is crucial for creating interactive applications.

#### **Model Selection and Configuration**

```python
models = {
    "llama3.1-8b": {"name": "Llama3.1-8b", "tokens": 8192, "developer": "Meta"}, 
    "llama3.1-70b": {"name": "Llama3.1-70b", "tokens": 8192, "developer": "Meta"}
}

col1, col2 = st.columns(2)

with col1:
    model_option = st.selectbox(
        "Choose a model:",
        options=list(models.keys()),
        format_func=lambda x: models[x]["name"]    
    )

if st.session_state.selected_model != model_option:
    st.session_state.messages = []
    st.session_state.selected_model = model_option

max_tokens_range = models[model_option]["tokens"]

with col2:
    max_tokens = st.slider(
        "Max Tokens:",
        min_value=512,
        max_value=max_tokens_range,
        value=max_tokens_range,
        step=512,
        help=f"Select the maximum number of tokens (words) for the model's response."
    )
```

- `st.selectbox`: Allows users to select a model from a dropdown menu, showcasing how Streamlit can be used for interactive selections.
- `st.slider`: Provides a slider for adjusting the maximum number of tokens for the model's response, demonstrating Streamlit’s capability for real-time user input adjustments.
- Conditional logic updates the session state when the selected model changes, clearing chat history to ensure relevant responses.

#### **Displaying and Managing Chat History**

```python
for message in st.session_state.messages:
    avatar = '🤖' if message["role"] == "assistant" else '🦔'
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
```

- Iterates through chat history and uses `st.chat_message` to display messages with appropriate avatars. This feature of Streamlit makes it easy to build interactive chat applications with user and assistant roles.

#### **Handling User Input and Generating Responses**

```python
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
```

- `st.chat_input`: Provides an input field for users to enter their prompt, integrating user interaction directly into the app.
- The response is fetched from the Cerebras API and displayed in the chat. This shows how Streamlit handles API interactions and updates the UI based on real-time data.

### Deploying a Streamlit App

To deploy your Streamlit app, follow these steps:

1. **Prepare Your Environment:**
   - Ensure you have all necessary dependencies listed in a `requirements.txt` file. For the provided app, this would include `streamlit`, `cerebras`, and any other libraries you use.

2. **Push to a Version Control System:**
   - Commit your code to a version control system like Git and push it to a repository (e.g., GitHub).

3. **Deploy to Streamlit Community Cloud:**
   - **Create a Streamlit Account**: If you don't already have one, create a Streamlit account at [Streamlit Community Cloud](https://streamlit.io/cloud).
   - **Link Your Repository**: Go to your Streamlit dashboard, and click on "New app". Connect your GitHub repository and select the branch that contains your Streamlit app.
   - **Deploy**: Streamlit will automatically deploy your app. You can see real-time logs and updates on the deployment status.

4. **Deploy to Other Cloud Providers (Optional):**
   - You can also deploy your Streamlit app on other cloud platforms like AWS, Google Cloud, or Azure. This involves setting up a virtual machine or container to host the app and configuring environment variables and security settings.

5. **Share Your App:**
   - Once deployed, you can share the URL with others to access your app. Ensure that any sensitive information, like API keys, is handled securely and not exposed in the code or public repositories.

By following these steps, you can easily deploy your Streamlit app and make it accessible to users around the world.