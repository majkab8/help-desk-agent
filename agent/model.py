import os
from dotenv import load_dotenv
from google.genai import types

load_dotenv()
model = os.getenv("MODEL_NAME", "gemini-2.5-flash")