# Memory module for deep-agent-swarm
from memory.chat_store import ChatStore
from memory.summary_store import SummaryStore
from memory.semantic_memory import SemanticMemory
from memory.context_assembler import ContextAssembler

# Global singleton instances
chat_store = ChatStore()
summary_store = SummaryStore()
semantic_memory = SemanticMemory()
context_assembler = ContextAssembler(chat_store, summary_store, semantic_memory)
