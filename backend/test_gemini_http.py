import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = httpx.get(url, timeout=10.0)
    data = response.json()
    print("Available model names:")
    for model in data.get("models", []):
        print(f" - {model['name']}")
except Exception as e:
    print(f"Error: {e}")
