# backend/memory.py

from collections import deque
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from config import get_settings

settings = get_settings()


class ConversationMemory:
    """
    Sliding window memory — keeps only the last N messages
    for low latency and efficient token usage.
    """

    def __init__(self, max_messages: int = None):
        self.max_messages = max_messages or settings.MAX_MEMORY_MESSAGES
        self._messages: deque[BaseMessage] = deque(maxlen=self.max_messages)

    def add_user_message(self, content: str) -> None:
        self._messages.append(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        self._messages.append(AIMessage(content=content))

    def get_messages(self) -> list[BaseMessage]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def to_dict_list(self) -> list[dict]:
        """Serializable format for API responses."""
        result = []
        for msg in self._messages:
            result.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
            })
        return result


# In-memory session store: session_id -> ConversationMemory
_sessions: dict[str, ConversationMemory] = {}


def get_memory(session_id: str) -> ConversationMemory:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationMemory()
    return _sessions[session_id]


def delete_memory(session_id: str) -> None:
    _sessions.pop(session_id, None)