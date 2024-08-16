# set CEREBRAS_API_KEY in the secrets

import os
from cerebras.cloud.sdk import Cerebras

# Create the Cerebras client
client = Cerebras(
    # This is the default and can be omitted
    api_key=os.environ.get("CEREBRAS_API_KEY"),
)

# Initialize the chat history
chat_history = []

while True:
    # Get user input from the console
    user_input = input("User: ")
    user_message = {"role": "user", "content": user_input}
    
    # Append the user input to the chat history
    chat_history.append(user_message)

    response = client.chat.completions.create(
    messages=[user_message],
    model="llama3.1-8b",
)
    # Append the user's response to the chat history
    chat_history.append({
      "role": "assistant",
      "content": response.choices[0].message.content
  })
    
    # Display the response
    print("Assistant:", response.choices[0].message.content)

    # Extract values
    total_tokens = response.usage.total_tokens
    total_time = response.time_info.total_time

    # Calculate tokens per second
    tokens_per_second = total_tokens / total_time

    # Display the tokens per second
    print("(Tokens per second: " + str(tokens_per_second) + ")")
    print("")