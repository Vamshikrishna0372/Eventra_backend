from google import genai
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

async def test():
    print(f"Using API Key: {API_KEY[:10]}...")
    client = genai.Client(api_key=API_KEY)
    try:
        print("Available Flash models:")
        for m in client.models.list():
            if "flash" in m.name.lower():
                print(f"- {m.name}")
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(test())
