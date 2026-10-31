from google import genai
from google.genai import types
from agent.config import GEMINI_MODEL
from agent.prompt import SYSTEM_PROMPT
from agent.tools.bookings import get_booking
from agent.tools.policies import search_policies
from agent.tools.refunds import calculate_refund


class GeminiModel:
    def __init__(self):
        self.client = genai.Client(http_options=types.HttpOptions(timeout=120_000))

        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[search_policies, get_booking, calculate_refund],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),

        )

    def generate(self, contents):
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=self.config,
        )
        return response
