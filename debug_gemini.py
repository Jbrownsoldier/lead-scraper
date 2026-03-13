import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

def test_genai_new_sdk():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Testing API Key: {api_key[:8]}...")
    
    client = genai.Client(api_key=api_key)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents="What is the current weather in London?",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error Detail: {e}")

if __name__ == "__main__":
    test_genai_new_sdk()
