from typing import TypedDict, List, Annotated, Literal, Optional
from pydantic import BaseModel, Field
import operator

from langchain_core.messages import BaseMessage

def clearable_add(a: list | None, b: list | str | None) -> list:
    if b == "CLEAR":
        return []
    if not a:
        a = []
    if not b:
        b = []
    return a + b

# ============================================================
# Phase 1: Semantic Models (Planner output — no execution awareness)
# ============================================================

class QueryAnalysis(BaseModel):
    """Purely semantic understanding of the user's query."""
    intent: Literal[
        "information_request", "comparison", "recommendation",
        "calculation", "explanation", "live_data", "creative",
        "conversational", "action_request"
    ]
    domain: str = Field(description="Domain of the query, e.g. 'sports', 'finance', 'programming', 'science', 'people'")
    query_type: Literal[
        "fact_lookup", "deep_research", "live_score", "news",
        "shopping", "coding", "opinion", "tutorial", "comparison",
        "calculation", "general"
    ]
    complexity: Literal["simple", "medium", "high"]
    estimated_tasks: int = Field(default=1, ge=1, le=10, description="Estimated number of sub-tasks needed")
    parallelizable: bool = Field(default=False, description="Whether sub-tasks can run in parallel")
    reasoning_strategy: Literal[
        "none", "summarize", "compare", "timeline", "calculate",
        "explain", "verify", "synthesize", "decompose", "multi_hop"
    ] = "none"

class KnowledgeAnalysis(BaseModel):
    """Describes the characteristics of the knowledge being requested."""
    knowledge_type: Literal["static", "semi_dynamic", "dynamic", "live"]
    time_sensitivity: Literal["none", "recent", "today", "live"]
    expected_change_frequency: Literal["never", "yearly", "monthly", "weekly", "daily", "hourly", "realtime"] = "never"
    freshness_window: Optional[str] = Field(default=None, description="e.g. '24h', '7d', '30d', '30s', null")
    volatility: Literal["low", "medium", "high", "extreme"] = "low"
    requires_recent_information: bool = False

class VerificationStrategy(BaseModel):
    """Describes the verification needs for this query."""
    required: bool = False
    confidence_target: float = Field(default=0.8, ge=0.0, le=1.0)

class AnswerContract(BaseModel):
    """Tells the composer exactly how to build the final response."""
    template: str = Field(description="e.g. 'fact_card', 'deep_report', 'tutorial', 'shopping_comparison', 'match_summary'")
    depth: Literal["brief", "short", "medium", "detailed", "comprehensive"] = "medium"
    must_answer: List[str] = Field(default_factory=list, description="Key aspects that MUST be addressed")
    optional: List[str] = Field(default_factory=list, description="Nice-to-have aspects")
    ignore: List[str] = Field(default_factory=list, description="Explicitly out-of-scope topics")

class PlannerOutput(BaseModel):
    """Complete semantic analysis from the Planner. No execution details."""
    query_analysis: QueryAnalysis
    knowledge_analysis: KnowledgeAnalysis
    verification: VerificationStrategy
    answer_contract: AnswerContract

# ============================================================
# Phase 2: Execution Models (Execution Planner — bridges semantic to execution)
# ============================================================

class ExecutionStrategy(BaseModel):
    """Output of the Execution Planner. Decides HOW to solve the problem."""
    execution_mode: Literal["internal_reasoning", "web_search", "live_data", "hybrid"]
    needs_retrieval: bool = False
    required_capabilities: List[str] = Field(
        default_factory=list,
        description="e.g. ['general_search'], ['live_score'], ['shopping', 'news']"
    )
    reasoning_strategy: str = Field(default="none", description="Forwarded from planner for the composer")
    max_sources: int = Field(default=5, ge=1, le=20)

# ============================================================
# Phase 3: Orchestrator Models (Agent routing)
# ============================================================

class Assignment(BaseModel):
    question: str
    priority: Literal["high", "medium", "low"]
    capability: str = Field(description="Required capability, e.g. 'general_search', 'news', 'shopping', 'live_score', 'finance', 'coding'")
    search_prompt: str
    needs_deep_search: bool = False

class OrchestratorOutput(BaseModel):
    research_goal: str
    assignments: List[Assignment]

# ============================================================
# Phase 4: Data / Evidence Models (unchanged from before)
# ============================================================

class Source(BaseModel):
    title: str
    url: str
    content: str
    source_type: str

class SearchResult(BaseModel):
    question: str
    sources: List[Source]

class CriticOutput(BaseModel):
    needs_more_research: bool
    follow_up_questions: list[str]
    critique: str

class TrustDimensions(BaseModel):
    source_count_score: int = Field(le=100, ge=0)
    source_authority_score: int = Field(le=100, ge=0)
    source_agreement_score: int = Field(le=100, ge=0)
    recency_score: int = Field(le=100, ge=0)
    fact_checker_verdict_score: int = Field(le=100, ge=0)

class VerifiedClaim(BaseModel):
    claim: str
    trust_score: int = Field(le=100, ge=0)
    trust_dimensions: TrustDimensions | None = None
    evidence: str
    verified: bool
    citations: List[str] = Field(default_factory=list)

class IntentOutput(BaseModel):
    intent: Literal["simple", "complex"]

class FactCheckOutput(BaseModel):
    verified_claims: Annotated[List[VerifiedClaim], operator.add]

class Chunk(BaseModel):
    content: str
    source_url: str
    relevance_score: float = 0.0

# ============================================================
# Phase 5: Structured Response Models (Composer output)
# ============================================================

class ReportSection(BaseModel):
    heading: str
    content: str

class StructuredResponse(BaseModel):
    """Structured output from the Response Composer. Presentation-independent."""
    title: str
    summary: str
    sections: List[ReportSection] = Field(default_factory=list)
    confidence_score: Optional[float] = None

# Legacy model kept for backward compat with fast_search path
class FinalReport(BaseModel):
    executive_summary: str
    key_findings: List[str]
    conclusion: str
    confidence_score: float | None = None

class RetrievalManagerOutput(BaseModel):
    """Raw evidence gathered from RAG and Web Search."""
    query: str
    pdf_contexts: List[str] = Field(default_factory=list)
    web_contexts: List[str] = Field(default_factory=list)
    total_sources_gathered: int

class KnowledgeGatewayOutput(BaseModel):
    """Cleaned, deduplicated, and formatted evidence ready for orchestration."""
    cleaned_context: str
    key_entities: List[str] = Field(default_factory=list)
    summary: str

class RetrievalManagerOutput(BaseModel):
    """Raw evidence gathered from RAG and Web Search."""
    query: str
    pdf_contexts: List[str] = Field(default_factory=list)
    web_contexts: List[str] = Field(default_factory=list)
    total_sources_gathered: int

class KnowledgeGatewayOutput(BaseModel):
    """Cleaned, deduplicated, and formatted evidence ready for orchestration."""
    cleaned_context: str
    key_entities: List[str] = Field(default_factory=list)
    summary: str

class CompareRouterOutput(BaseModel):
    needs_web_search: bool
    research_topics: str = ""

class QueryRewriterOutput(BaseModel):
    """Output of the Query Rewriter — coreference resolution."""
    original_query: str
    rewritten_query: str
    was_rewritten: bool

class QueryRouterOutput(BaseModel):
    """Output of the Query Router — decides which memory sources to retrieve from."""
    route: Literal["docs_only", "conversation_only", "docs_and_web", "web_only", "no_retrieval"]
    reasoning: str

# ============================================================
# Phase 6: Subgraph State Models
# ============================================================

class AssignmentState(TypedDict):
    assignment: Assignment

# ============================================================
# Phase 7: Main Graph State
# ============================================================

class FINALSTATE(TypedDict):
    user_query: str
    messages: list[BaseMessage]
    search_mode: Literal["simple", "complex"]
    intent_output: IntentOutput

    # Intermediate analysis results (individual nodes)
    query_analysis_result: QueryAnalysis
    knowledge_analysis_result: KnowledgeAnalysis

    # Semantic analysis (combined PlannerOutput)
    planner_output: PlannerOutput

    # Execution strategy (Execution Planner output)
    execution_strategy: ExecutionStrategy

    # Pre-orchestration Retrieval
    retrieval_manager_output: RetrievalManagerOutput
    knowledge_gateway_output: KnowledgeGatewayOutput
    compare_router_output: CompareRouterOutput

    # Orchestrator output
    decompose_tasks: OrchestratorOutput

    # Evidence pipeline
    sources: Annotated[List[Source], clearable_add]
    deduped_sources: List[Source]
    chunks: Annotated[List[Chunk], clearable_add]
    reranked_chunks: List[Chunk]
    fetched_content: str
    synthesized_context: str

    # Verification
    fact_checker: FactCheckOutput
    critic_output: CriticOutput

    # Response
    structured_response: StructuredResponse
    final_report: str  # Final rendered markdown

    # Control
    iteration_count: int
    initial_search_context: str

    # Memory architecture
    rewritten_query: str  # Coreference-resolved query
    query_rewriter_output: QueryRewriterOutput
    query_router_output: QueryRouterOutput
    assembled_context: str  # Output of context_assembler
    _thread_id: str  # Thread ID for memory lookups (injected at invocation)
