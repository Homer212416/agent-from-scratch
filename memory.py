from typing import Optional, Callable

class ConversationMemory:
    def __init__(self, max_tokens: int = 2000, summarizer: Optional[Callable] = None):
        self.messages = []
        self.summary = ""
        self.max_tokens = max_tokens
        self.summarizer = summarizer

    def _count_tokens(self, content:str) -> int:
        return len(content)//4

    def _total_tokens(self) -> int:
        return sum(self._count_tokens(msg["content"]) for msg in self.messages)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if self._total_tokens() > self.max_tokens * 0.8:
            self._compress()

    def _compress(self) -> None:
        print("! The agent will compress its memory.")
        # Keep the last 2 messages (1 pairs), summarize the rest
        to_summarize = self.messages[:-2]
        self.messages = self.messages[-2:]

        if not to_summarize:
            return

        if self.summarizer:
            new_summary = self.summarizer(to_summarize, self.summary)
        else:
            # stub when there is no summarizer
            new_summary = f"[Summary of {len(to_summarize)} messages]"

        self.summary = new_summary

        print(f"! [Full Summary]: {self.summary}\n")

    def get_context(self) -> list:
        result = []
        if self.summary:
            result.append({"role": "system", "content": f"Summary of earlier conversation:\n{self.summary}"})
        result.extend(self.messages)
        return result

    def clear(self) -> None:
        self.messages = []
        self.summary = ""

if __name__ == "__main__":
    mem = ConversationMemory(max_tokens=50)
    for i in range(5):
        mem.add_message("user",f"This is user message number {i}")
        mem.add_message("assistant",f"This is assistant message number {i}")
        print(f"Message remaining: {len(mem.messages)}")
        print(mem.get_context())