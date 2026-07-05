"""
Semantic Memory — Long-term user facts and preferences.
Only stores important, extracted facts — NOT raw chat messages.
Examples: "user prefers Python", "user works in healthcare", "user's project uses FastAPI"
"""


class SemanticMemory:
    """In-memory per-thread semantic fact store."""

    def __init__(self):
        # {thread_id: [fact_string, ...]}
        self._facts: dict[str, list[str]] = {}

    def add_fact(self, thread_id: str, fact: str):
        """Store a semantic fact for the thread."""
        if thread_id not in self._facts:
            self._facts[thread_id] = []
        # Avoid duplicates
        if fact not in self._facts[thread_id]:
            self._facts[thread_id].append(fact)

    def get_facts(self, thread_id: str) -> list[str]:
        """Return all stored semantic facts for this thread."""
        return self._facts.get(thread_id, [])

    def format_facts(self, thread_id: str) -> str:
        """Format facts as a readable block for prompt injection."""
        facts = self.get_facts(thread_id)
        if not facts:
            return ""
        return "Known facts about this user/conversation:\n" + "\n".join(f"- {f}" for f in facts)
