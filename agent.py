import os
from zhipuai import ZhipuAI
from memory import ConversationMemory
from retrieval import SemanticRetrievalStore
from typing import Optional
import json
import time

from errors import APIKeyError, AgentError, MemoryFileError

class Agent:

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4-flash",
        max_tokens: int = 1000,
        persist_path: Optional[str] = "semantic_store.json",
        top_k: int = 3,
    ):
        """Create an agent. Falls back to the ZAI environment variable if
        api_key is not provided. Loads existing memory from persist_path
        if it exists."""
    
        self.model = model
        self.top_k = top_k
        self.persist_path = persist_path

        if api_key is None:
            api_key = os.getenv("ZAI")

        if not api_key:
            raise APIKeyError(
                "API key required. Either pass api_key=... or set "
                "the ZAI environment variable in your .env file."
            )

        self.client = ZhipuAI(api_key=api_key)

        self.memory = ConversationMemory(
            max_tokens=max_tokens,
            summarizer=self._summarize
        )

        if persist_path and os.path.exists(persist_path):
            try:
                # already have a store file
                self.retrieval = SemanticRetrievalStore.load(persist_path)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                raise MemoryFileError(
                    f"Memory file at '{persist_path}' is corrupted or incompatible: {e}. "
                    f"Delete it to start fresh, or restore from a backup."
                )

        else:
            # a brand new store
            self.retrieval = SemanticRetrievalStore()


    def _summarize(self, messages: list, existing_summary: str) -> str:
        """Compress a batch of messages into an updated summary. Called
        automatically by ConversationMemory when the working window fills."""
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


    def _call_llm(self, messages: list, max_retries: int = 1) -> str:
        """Call the LLM with one retry on failure. Raises AgentError if
        all attempts fail."""
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                
                time.sleep(1)
                if (attempt + 1 > max_retries):
                    raise AgentError(
                        f"LLM call failed after {max_retries + 1} attempts: {e}"
                    )


    def _build_context(self, retrieved_docs: list) -> list:
        """Assemble the final prompt: summary + retrieved docs + working window."""
        context = self.memory.get_context()
        if retrieved_docs:
            context.insert(1, {
                "role": "system",
                "content": "Possibly relevant earlier context:\n" + 
                            "\n".join(f"- {doc}" for doc in retrieved_docs)
            })
        return context


    def chat(self, user_message: str) -> str:

        """Send a message, get a reply. Updates memory and retrieval store,
        and may trigger summarization if the window is full."""

        # Search before adding — otherwise the current message would match itself
        # with perfect similarity and crowd out genuinely relevant history.
        
        retrieved_docs = self.retrieval.search(user_message, top_k=self.top_k)

        self.memory.add_message("user", user_message)

        self.retrieval.add(user_message)

        context = self._build_context(retrieved_docs)

        reply = self._call_llm(context)

        self.memory.add_message("assistant", reply)

        return reply


    def save(self) -> None:
        """Persist the retrieval store to disk."""
        if self.persist_path:
            self.retrieval.save(self.persist_path)

    def close(self) -> None:
        """Save and release resources. Call this when done with the agent."""
        self.save()


    

