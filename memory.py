
class ConversationMemory:
    def __init__(self):
        self.messages = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_context(self) -> str:
        return "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in self.messages
        )

    def clear(self) -> None:
        self.messages = []