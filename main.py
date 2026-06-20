import os
from dotenv import load_dotenv
from agent import Agent

def main():
    load_dotenv()
    agent = Agent(api_key=os.getenv("ZAI"))

    print("Agent ready. Type 'quit' to exit.")
    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        reply = agent.chat(user_input)
        print(f"Agent: {reply}")

    agent.close()

if __name__ == "__main__":
    main()