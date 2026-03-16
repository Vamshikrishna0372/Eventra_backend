import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def test():
    print(f"Using API Key: {API_KEY[:10]}...")
    genai.configure(api_key=API_KEY, transport='rest')
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say hello")
        print("Response:", response.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test()
