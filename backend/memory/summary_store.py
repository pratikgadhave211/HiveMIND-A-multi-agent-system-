"""
Summary Store — Running conversation summaries.
Updated every 15 messages to preserve long-term context without exploding prompt length.
The summary is a condensed representation of the entire conversation up to that point.
"""
from core.llm import llm


class SummaryStore:
    """In-memory per-thread running conversation summary."""

    def __init__(self):
        # {thread_id: summary_text}
        self._summaries: dict[str, str] = {}
        # {thread_id: turn_count_at_last_summary}
        self._last_summary_at: dict[str, int] = {}

    def get_summary(self, thread_id: str) -> str:
        """Return the current running summary for this thread."""
        return self._summaries.get(thread_id, "")

    def update_summary(self, thread_id: str, new_summary: str, turn_count: int):
        """Replace the running summary and record when it was last updated."""
        self._summaries[thread_id] = new_summary
        self._last_summary_at[thread_id] = turn_count

    def should_update(self, thread_id: str, current_turn_count: int) -> bool:
        """Return True if we've accumulated 15+ new turns since last summary."""
        last = self._last_summary_at.get(thread_id, 0)
        return (current_turn_count - last) >= 15

    async def generate_and_update(self, thread_id: str, chat_turns: list, current_turn_count: int):
        """Generate a new running summary from the conversation and the previous summary."""
        existing_summary = self.get_summary(thread_id)

        # Format recent turns (since last summary) for the LLM
        last_at = self._last_summary_at.get(thread_id, 0)
        new_turns = chat_turns[last_at:]
        turns_text = "\n".join([
            f"[{'User' if t.role == 'user' else 'Assistant'}]: {t.content[:300]}"
            for t in new_turns
        ])

        prompt = f"""You are a conversation summarizer. Create a concise running summary that captures all important information from this conversation.

PREVIOUS SUMMARY:
{existing_summary if existing_summary else "(No previous summary — this is the first summarization.)"}

NEW CONVERSATION TURNS:
{turns_text}

Write a concise summary (max 300 words) that:
1. Preserves all key facts, decisions, and topics discussed
2. Integrates the new turns with the previous summary
3. Drops redundant or trivial small talk
4. Maintains chronological awareness of what was discussed when

UPDATED SUMMARY:"""

        try:
            response = await llm.ainvoke(prompt)
            summary_text = response.content if hasattr(response, 'content') else str(response)
            self.update_summary(thread_id, summary_text.strip(), current_turn_count)
            print(f"Summary Store: Updated summary for thread {thread_id[:8]}... at turn {current_turn_count}")
        except Exception as e:
            print(f"Summary generation failed: {e}")
