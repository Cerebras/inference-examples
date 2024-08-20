import streamlit as st
import pandas as pd
from cerebras.cloud.sdk import Cerebras
import json
import webbrowser

repl_link = ""

# Initialize Cerebras client
@st.cache_resource
def get_cerebras_client(api_key):
    return Cerebras(api_key=api_key)

st.title("Synthetic Data Generator using Cerebras")

# Sidebar for API key input
with st.sidebar:
    if st.button('Spin up your own on Repl.it :material/code:', type='secondary'):
        webbrowser.open(repl_link)
    st.title("Settings")
    api_key = st.text_input("Enter your Cerebras API Key:", type="password")

if not api_key:
    st.warning("Please enter your Cerebras API Key in the sidebar to proceed.")
    st.stop()

cerebras_client = get_cerebras_client(api_key)

# Data generation options
st.subheader("Define Data Generation Parameters")
num_rows = st.number_input("Number of rows to generate:", min_value=1, max_value=1000, value=10)
schema = st.text_area("Define your data schema (JSON format):", 
                      value='''{
    "name": "string",
    "age": "integer",
    "email": "email",
    "salary": "float"
}''')

try:
    schema_dict = json.loads(schema)
except json.JSONDecodeError:
    st.error("Invalid JSON schema. Please check your input.")
    st.stop()

# Function to generate synthetic data using Cerebras
def generate_synthetic_data(num_rows, schema):
    prompt = f"""Generate {num_rows} rows of synthetic data based on the following schema:
    {json.dumps(schema, indent=2)}
    
    Return the data as a JSON object with a single key 'data' containing an array of objects.
    Do not include any backticks or other formatting characters in your response."""
    
    try:
        response = cerebras_client.chat.completions.create(
            model="llama3.1-70b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates synthetic data in valid JSON format without any additional formatting characters."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            stream=False
        )
        
        raw_content = response.choices[0].message.content
        st.text("Raw API Response:")
        st.code(raw_content, language="json")
        
        # Strip backticks and whitespace
        cleaned_content = raw_content.strip('` \n')
        
        json_data = json.loads(cleaned_content)
        if 'data' not in json_data or not isinstance(json_data['data'], list):
            raise ValueError("Response does not contain a 'data' array")
        
        return pd.DataFrame(json_data['data'])
    
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {str(e)}")
        st.text("Problematic JSON string:")
        st.code(cleaned_content, language="json")
        raise
    except Exception as e:
        st.error(f"Error processing the response: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            error_json = e.response.json()
            if 'failed_generation' in error_json:
                st.text("Failed JSON generation:")
                st.code(error_json['failed_generation'], language="json")
        raise

if st.button("Generate Data"):
    with st.spinner("Generating synthetic data..."):
        try:
            df = generate_synthetic_data(num_rows, schema_dict)
            st.success(f"Successfully generated {num_rows} rows of synthetic data!")
            st.write(df)

            # Download option
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV",
                csv,
                "synthetic_data.csv",
                "text/csv",
                key='download-csv'
            )
        except Exception as e:
            st.error(f"An error occurred while generating data: {str(e)}")

st.info("Note: This app uses the Cerebras API to generate synthetic data based on your specified schema.")