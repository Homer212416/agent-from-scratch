import os

from zhipuai import ZhipuAI
from memory import ConversationMemory
from dotenv import load_dotenv
from retrieval import RetrievalStore
from retrieval import SemanticRetrievalStore

load_dotenv()

key=os.getenv("ZAI")

client = ZhipuAI(api_key=key)

def summerizer(messages:list, existing_summary:str)->str:

    messages_text = "\n".join(
        f"{msg['role']}: {msg['content']}" for msg in messages
    )

    system_prompt = f"""You are a memory summarizer. Given the following conversation, 
extract and summarize the important information concisely.

Focus on:
- User and assistant identities and names
- Any tasks or todos the user mentioned
- Key facts the user emphasized
- Anything the user might ask about later

Provide only the summary, no introduction or conclusion."""   

    user_prompt = f"""
Previous summary (if any):
{existing_summary}

New conversation to summarize:
{messages_text}
    """

    response = client.chat.completions.create(
        model="glm-5",
        messages=[{"role":"system","content":system_prompt},
        {"role":"user","content":user_prompt}]
    )

    return response.choices[0].message.content

memory = ConversationMemory(max_tokens=1000,summarizer=summerizer)
store = RetrievalStore()

semantic_store = SemanticRetrievalStore()

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break

    if not user_input.strip():
        continue
    
    memory.add_message("user", user_input)

    # Retrieve relevant context
    retrieved = store.search(user_input, top_k=3)

    semantic_retrieved = semantic_store.search(user_input, top_k=3)

    # Add to store
    store.add(user_input)

    semantic_store.add(user_input)

    context = memory.get_context()
        
    print("------------ Naive Retrieval -------------")
    print(f"[Retrieved]: {retrieved}\n")
    print("------------------------------------------")
    print("----------- Semantic Retrieval -----------")
    print(f"[Semantic Retrieved]: {semantic_retrieved}\n")
    print("------------------------------------------") 

    if semantic_retrieved:
        context.insert(1, {
            "role": "system",
            "content": "Possibly relevant earlier context:\n" + "\n".join(f"- {r}" for r in semantic_retrieved)
        })

    response = client.chat.completions.create(
        model="glm-5",
        messages=context 
    )
    
    assistant_reply = response.choices[0].message.content
    memory.add_message("assistant", assistant_reply)

    print()
    print("------------ Reply -------------")
    print(f"Assistant: {assistant_reply}\n")
    print(f"[Context length]: {sum(len(mem['content']) for mem in memory.get_context())} chars\n")
    print("------------------------------------------")       
    print() 
