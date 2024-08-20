## Got Data? Generating Synthetic Data with Cerebras

What's better than data? Synthetic data! (Occaisionally, of course). In this tutorial, we'll walk through developing a Streamlit application that generates synthetic data using the Cerebras API.

### Step 1: Set up your API Key

1. **Obtain Your API Key**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras API key, add it to the sidebar on the left.

### Step 2: Install dependencies

Let's make sure we have all of the requirements for this project installed!
```bash
pip install -r requirements.txt
```

### Step 3: Start generating data
Simply run `streamlit run main.py` to get started!

### Code Overview

#### Import Libraries

```python
import streamlit as st
import pandas as pd
from cerebras.cloud.sdk import Cerebras
import json
```

We start by importing the necessary libraries. **`streamlit`** is used to build the web application, **`pandas`** helps in managing and displaying the data, **`Cerebras`** provides the SDK to interact with the Cerebras API, and **`json`** handles JSON data parsing and manipulation.

#### Initialize the Cerebras Client

```python
@st.cache_resource
def get_cerebras_client(api_key):
    return Cerebras(api_key=api_key)
```

This function initializes the Cerebras client using the provided API key. The **`@st.cache_resource`** decorator ensures that the client is only created once and reused, improving performance by avoiding redundant initializations.

#### Set Up the Streamlit Interface

```python
st.title("Synthetic Data Generator using Cerebras")

with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Enter your Cerebras API Key:", type="password")

if not api_key:
    st.warning("Please enter your Cerebras API Key in the sidebar to proceed.")
    st.stop()
```

We set up the main page and sidebar for user inputs. The **`st.text_input`** widget collects the API key securely, and if it’s not provided, a warning message is shown and the app stops until the key is entered.

#### Define Data Generation Parameters

```python
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
```

We allow users to specify the number of rows of data and provide a JSON schema for data generation. The **`json.loads`** function parses the schema; if the schema is invalid, an error is displayed, and the app stops to prevent further issues.

#### Define the Data Generation Function

**1. Constructing the API Request Prompt**

```python
def generate_synthetic_data(num_rows, schema):
    prompt = f"""Generate {num_rows} rows of synthetic data based on the following schema:
    {json.dumps(schema, indent=2)}
    
    Return the data as a JSON object with a single key 'data' containing an array of objects.
    Do not include any backticks or other formatting characters in your response."""
```

This segment constructs a prompt for the Cerebras API that details the data generation requirements. It formats the schema in a readable JSON format and specifies that the data should be returned as a JSON object with a 'data' key.

**2. Making the API Request**

```python
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
```

This part sends the request to the Cerebras API. It specifies the model to use and provides the necessary messages to guide the API in generating the synthetic data as required by the prompt.

**3. Processing the API Response**

```python
        raw_content = response.choices[0].message.content
        st.text("Raw API Response:")
        st.code(raw_content, language="json")
        
        cleaned_content = raw_content.strip('` \n')
```

After receiving the response, we extract and display the raw JSON data for the user as output. We can then clean the data by removing any extraneous characters to prepare it for parsing.

**4. Parsing and Validating JSON Data**

```python
        json_data = json.loads(cleaned_content)
        if 'data' not in json_data or not isinstance(json_data['data'], list):
            raise ValueError("Response does not contain a 'data' array")
        
        return pd.DataFrame(json_data['data'])
```

We parse the cleaned JSON string into a dictionary and validate it to ensure it contains the expected 'data' key with a list value. If the data is valid, it is converted into a Pandas DataFrame so we can allow users to download it as a CSV (as shown in `Generate and Display Data`).

**5. Error Handling**

```python
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
```

This section handles errors that may occur during the JSON parsing or response processing stages. It displays appropriate error messages and problematic data to aid in troubleshooting if issues arise.

#### Generate and Display Data

```python
if st.button("Generate Data"):
    with st.spinner("Generating synthetic data..."):
        try:
            df = generate_synthetic_data(num_rows, schema_dict)
            st.success(f"Successfully generated {num_rows} rows of synthetic data!")
            st.write(df)

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
```

When the "Generate Data" button is pressed, the app generates the data by calling the `generate_synthetic_data` function we defined and displays a success message along with the dataframe. It also provides an option to download the data as a CSV file.