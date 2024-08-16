## Streamlining App UI: Streamlit & Cerebras

xxxx

picture goes here

### Step 1: Set up your API Key

1. **Obtain Your API Key**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key.

2. **Set the API Key as an Environment Variable**: For security, store your API key as a secret in your repl! Here's [more information](https://docs.replit.com/replit-workspace/workspace-features/secrets) on how to do that.

![setting a secret](https://gist.github.com/user-attachments/assets/25a2741e-859f-4ba3-a105-a78435e89fb4.png)

   This ensures that your API key is available to your script without hardcoding it directly.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API by using repl's built in `Shell`. Use the following command to install the library:

```bash
pip install https://cerebras-cloud-sdk.s3.us-west-1.amazonaws.com/test/cerebras_cloud_sdk-0.5.0-py3-none-any.whl
```

Go ahead and also run `pip install -r requirements.txt` to install other requirements as well!

### Step 3: Streamline your Streamlit Experience 
Press RUN and then run the command `streamlit run main.py` in Shell to interact with the UI.