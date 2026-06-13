import os

from zhipuai import ZhipuAI
from memory import ConversationMemory
from dotenv import load_dotenv

load_dotenv()

key=os.getenv("ZAI")

client = ZhipuAI(api_key=key)
memory = ConversationMemory()

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break

    if not user_input.strip():
        continue
    
    memory.add_message("user", user_input)
    
    response = client.chat.completions.create(
        model="glm-5",
        messages=memory.messages
    )
    
    assistant_reply = response.choices[0].message.content
    memory.add_message("assistant", assistant_reply)
    
    print(f"Assistant: {assistant_reply}\n")
    print(f"[Context length]: {len(memory.get_context())} chars\n")