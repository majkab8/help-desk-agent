from agent.model import GeminiModel
from agent.agent_loop import run_agent

def main():
    model = GeminiModel()
    print("CityWheels help desk assistant. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            break
        try:
            response = run_agent(user_input, model)
            print("Agent:", response["answer"])
            print()
        except Exception as error:
            print(f"Sorry, something went wrong: {error}.")
    print("Hope I answered all your questions. Goodbye.")

if __name__ == "__main__":
    main()