import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
CURRENT_TIME = datetime.fromisoformat("2026-06-10T09:00:00+02:00")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.6-flash"