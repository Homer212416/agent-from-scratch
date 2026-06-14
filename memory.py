
class ConversationMemory:
    def __init__(self, max_tokens: int = 2000):
        self.messages = []
        self.max_tokens = max_tokens

    def _count_tokens(self, content:str) -> int:
        return len(content)//4

    def _total_tokens(self) -> int:
        return sum(self._count_tokens(msg["content"]) for msg in self.messages)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._enforce_limit()

    def _enforce_limit(self) -> None:
        while self._total_tokens() > self.max_tokens and len(self.messages) >= 2:
            self.messages.pop(0)
            self.messages.pop(0)

    def get_context(self) -> str:
        return "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in self.messages
        )

    def clear(self) -> None:
        self.messages = []

if __name__ == "__main__":
    mem = ConversationMemory(max_tokens=50)
    for i in range(5):
        mem.add_message("user",f"This is user message number {i}")
        mem.add_message("assistant",f"This is assistant message number {i}")
        print(f"Message remaining: {len(mem.messages)}")
        print(mem.get_context())