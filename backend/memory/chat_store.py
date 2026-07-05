"""
Chat Store — Per-thread conversation history.
Stores raw conversation turns in-memory. Each turn records role, content, mode, and timestamp.
This is NOT embedded into the vector database. It is read directly for prompt injection.
"""
from dataclasses import dataclass, field
from typing import List, Literal
import time


@dataclass
class ChatTurn:
    role: Literal["user", "assistant"]
    content: str
    mode: Literal["simple", "complex"]
    timestamp: float = field(default_factory=time.time)


class ChatStore:
    """In-memory per-thread chat history. Thread-safe for single-process async."""

    def __init__(self):
        # {thread_id: [ChatTurn, ...]}
        self._store: dict[str, List[ChatTurn]] = {}

    def add_turn(self, thread_id: str, role: str, content: str, mode: str = "simple"):
        """Append a conversation turn for the given thread."""
        if thread_id not in self._store:
            self._store[thread_id] = []
        self._store[thread_id].append(ChatTurn(
            role=role,
            content=content,
            mode=mode,
        ))

    def get_recent_turns(self, thread_id: str, n: int = 10) -> List[ChatTurn]:
        """Return the last N turns. These are always injected directly into the prompt."""
        turns = self._store.get(thread_id, [])
        return turns[-n:]

    def get_all_turns(self, thread_id: str) -> List[ChatTurn]:
        """Return all turns for summarization."""
        return self._store.get(thread_id, [])

    def get_turn_count(self, thread_id: str) -> int:
        """Return total turn count for summary trigger logic."""
        return len(self._store.get(thread_id, []))

    def format_recent_turns(self, thread_id: str, n: int = 10) -> str:
        """Format recent turns as a readable string block for prompt injection."""
        turns = self.get_recent_turns(thread_id, n)
        if not turns:
            return ""
        lines = []
        for t in turns:
            role_label = "User" if t.role == "user" else "Assistant"
            lines.append(f"[{role_label}]: {t.content[:500]}")
        return "\n".join(lines)
