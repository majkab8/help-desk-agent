from dotenv import load_dotenv
from google import genai

load_dotenv()
model = genai.Client()