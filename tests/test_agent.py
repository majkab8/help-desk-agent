from google.genai import types

from agent.agent_loop import MAX_ITERATIONS, run_agent


def text_response(text):
    """A fake Gemini response with a final text answer."""
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text=text)])
            )
        ]
    )


def tool_call_response(name, args):
    """A fake Gemini response in which the model asks to call a tool."""
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))],
                )
            )
        ]
    )


class FakeModel:
    """Returns prepared responses one by one, without network or API key."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.received = []

    def generate(self, contents):
        self.received.append(list(contents))
        return self.responses.pop(0)


def test_agent_calls_refund_tool_and_returns_answer():
    model = FakeModel([
        tool_call_response("calculate_refund", {"booking_id": "CW-1002"}),
        text_response("You get 340 EUR back."),
    ])

    result = run_agent("How much do I get back for CW-1002?", model)

    assert result["answer"] == "You get 340 EUR back."
    assert result["tools_called"] == ["calculate_refund"]

    tool_message = model.received[1][-1]
    tool_result = tool_message.parts[0].function_response.response
    assert tool_result["total_refund_eur"] == 340.0


def test_agent_answers_without_tools():
    model = FakeModel([text_response("I can only help with CityWheels questions.")])

    result = run_agent("What is the capital of Australia?", model)

    assert result["answer"] == "I can only help with CityWheels questions."
    assert result["tools_called"] == []


def test_agent_handles_unknown_tool():
    model = FakeModel([
        tool_call_response("delete_everything", {}),
        text_response("Sorry, I cannot do that."),
    ])

    result = run_agent("Delete everything", model)

    assert result["answer"] == "Sorry, I cannot do that."
    assert result["tools_called"] == ["delete_everything"]


def test_agent_handles_unknown_booking():
    model = FakeModel([
        tool_call_response("get_booking", {"booking_id": "CW-9999"}),
        text_response("Booking CW-9999 was not found."),
    ])

    result = run_agent("Show me CW-9999", model)

    tool_result = model.received[1][-1].parts[0].function_response.response
    assert tool_result["found"] is False
    assert result["answer"] == "Booking CW-9999 was not found."


def test_agent_stops_after_max_iterations():
    model = FakeModel(
        [tool_call_response("get_booking", {"booking_id": "CW-1001"})] * MAX_ITERATIONS
    )

    result = run_agent("Loop forever", model)

    assert "contact the staff" in result["answer"]
    assert len(result["tools_called"]) == MAX_ITERATIONS