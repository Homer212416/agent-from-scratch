import os
from zhipuai import ZhipuAI
from memory import ConversationMemory
from retrieval import SemanticRetrievalStore
from typing import Optional


class Agent:
    def __init__(
        self,
        api_key: str,
        model: str = "glm-4-flash",
        max_tokens: int = 1000,
        persist_path: Optional[str] = "semantic_store.json",
        top_k: int = 3,
    ):
        self.model = model
        self.top_k = top_k
        self.persist_path = persist_path

        self.client = ZhipuAI(api_key=api_key)

        self.memory = ConversationMemory(
            max_tokens=max_tokens,
            summarizer=self._summarize
        )

        if persist_path and os.path.exists(persist_path):
            self.retrieval = SemanticRetrievalStore.load(persist_path)
        else:
            self.retrieval = SemanticRetrievalStore()


    def _summarize(self, messages: list, existing_summary: str) -> str:
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

    Conversation to summarize:
    {messages_text}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content


    def _call_llm(self, messages: list) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content


    def _build_context(self, retrieved_docs: list) -> list:

        context = self.memory.get_context()
        if retrieved_docs:
            context.insert(1, {
                "role": "system",
                "content": "Possibly relevant earlier context:\n" + 
                            "\n".join(f"- {doc}" for doc in retrieved_docs)
            })
        return context


    def chat(self, user_message: str) -> str:
        
        # 1. retrieve relevant past context
        retrieved_docs = self.retrieval.search(user_message, top_k=self.top_k)

        # 2. add user message to memory (may trigger summarization internally)
        self.memory.add_message("user", user_message)

        # 3. add user message to retrieval store
        self.retrieval.add(user_message)

        # 4. build the full prompt
        context = self._build_context(retrieved_docs)

        # 5. call the LLM
        reply = self._call_llm(context)

        # 6. update memory with the reply
        self.memory.add_message("assistant", reply)

        # 7. return the reply
        return reply


    def save(self) -> None:
        if self.persist_path:
            self.retrieval.save(self.persist_path)


    def close(self) -> None:
        self.save()


    

