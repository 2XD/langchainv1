import os
import time
from openai import AzureOpenAI
from openai._exceptions import APIConnectionError, OpenAIError
from dotenv import load_dotenv
load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello! Can you confirm this works?"}
]
#trying out a retry loop cause Github said it might be something to do with "rate limiting"
MAX_RETRIES = 3
RETRY_DELAY = 5  #this is in seconds.

for attempt in range(1, MAX_RETRIES + 1):
    try:
        print(f"[Attempt {attempt}] Sending request to Azure OpenAI...")
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=messages
        )
        print("[Success] Azure OpenAI responded:")
        print(response.choices[0].message.content)
        break  # success

    except APIConnectionError as e:
        print(f"[Error] API connection failed (network or endpoint): {e}")
        if attempt < MAX_RETRIES:
            print(f"Retrying in {RETRY_DELAY} seconds...\n")
            time.sleep(RETRY_DELAY)
        else:
            print("Max retries reached. Still getting connection errors.")
    
    except OpenAIError as e:
        print(f"[Fatal Error] Unexpected OpenAI error: {e}")
        break
    
    except Exception as e:
        print(f"[Unhandled Exception] {type(e).__name__}: {e}")
        break
