import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_models():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Testing API Key: {api_key[:8]}...")
    
    genai.configure(api_key=api_key)
    
    try:
        print("Listing models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
