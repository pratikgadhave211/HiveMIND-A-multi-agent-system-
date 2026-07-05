"""
Context Assembler — Merges all memory sources into a single prompt block.
This is the central orchestrator that combines:
1. Running conversation summary
2. Last 10 conversation turns (always, no retrieval)
3. Semantic memory facts
4. Retrieved document chunks (if query router said docs needed)
5. Retrieved web chunks (if query router said web needed)
"""
from memory.chat_store import ChatStore
from memory.summary_store import SummaryStore
from memory.semantic_memory import SemanticMemory


class ContextAssembler:
    """Merges isolated memory sources into a unified context block for the LLM."""

    def __init__(self, chat_store: ChatStore, summary_store: SummaryStore, semantic_memory: SemanticMemory):
        self.chat_store = chat_store
        self.summary_store = summary_store
        self.semantic_memory = semantic_memory

    def assemble_context(
        self,
        thread_id: str,
        doc_chunks: list[str] | None = None,
        web_context: str = "",
    ) -> str:
        """
        Build the full context block from all isolated memory sources.
        Returns a formatted string ready for prompt injection.
        """
        sections = []

        # 1. Running conversation summary (long-term context)
        summary = self.summary_store.get_summary(thread_id)
        if summary:
            sections.append(f"=== CONVERSATION SUMMARY (Long-term context) ===\n{summary}")

        # 2. Recent conversation turns (always included, no retrieval needed)
        recent = self.chat_store.format_recent_turns(thread_id, n=10)
        if recent:
            sections.append(f"=== RECENT CONVERSATION (Last 10 turns) ===\n{recent}")

        # 3. Semantic memory (user facts/preferences)
        facts = self.semantic_memory.format_facts(thread_id)
        if facts:
            sections.append(f"=== USER CONTEXT ===\n{facts}")

        # 4. Retrieved document chunks (RAG - from uploaded PDFs only)
        if doc_chunks:
            doc_text = "\n\n".join(doc_chunks[:10])  # Limit to top 10 chunks
            sections.append(f"=== RETRIEVED DOCUMENT CONTEXT ===\n{doc_text}")

        # 5. Web search context (from orchestrator pipeline)
        if web_context:
            sections.append(f"=== WEB SEARCH EVIDENCE ===\n{web_context}")

        if not sections:
            return ""

        return "\n\n".join(sections)
