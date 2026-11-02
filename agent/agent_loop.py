from google.genai import types
from agent.tools.bookings import get_booking
from agent.tools.policies import search_policies
from agent.tools.refunds import calculate_refund

MAX_ITERATIONS = 6
TOOLS = {"get_booking": get_booking,
         "search_policies": search_policies,
         "calculate_refund": calculate_refund,
         }


def run_agent(question, model):
    contents = [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]
    tools_called = []

    for _ in range(MAX_ITERATIONS):
        response = model.generate(contents)
        if not response.function_calls:
            return {"answer": response.text,
                    "tools_called": tools_called,
                    }
        contents.append(response.candidates[0].content)
        response_parts = []
        for call in response.function_calls:
            tools_called.append(call.name)
            if call.name not in TOOLS:
                result = {"error": f"Unknown tool: {call.name}"}
            else:
                try:
                    result = TOOLS[call.name](**call.args)
                except Exception as error:
                    result = {"error": f"Tool {call.name} failed: {error}"}
            response_parts.append(
                types.Part.from_function_response(name=call.name, response=result)
            )
        contents.append(types.Content(role="user", parts=response_parts))

    return {"answer": "Sorry I couldn't answer your question."
                      " Please contact the staff: help@citywheels.example, +48 000 000 000",
            "tools_called": tools_called,
            }