from langgraph.graph import START, END, StateGraph
from agents.state import FINALSTATE
from agents.nodes.orchestrator import CAPABILITY_TO_AGENT

# ============================================================
# Node Imports
# ============================================================

# Memory-aware Query Intelligence
from agents.nodes.query_rewriter import query_rewriter_node
from agents.nodes.query_router import query_router_node

# Semantic Pipeline
from agents.nodes.intent_router import intent_router_node
from agents.nodes.query_analyzer import query_analyzer_node
from agents.nodes.knowledge_analyzer import knowledge_analyzer_node
from agents.nodes.planner import answer_contract_builder_node
from agents.nodes.execution_planner import execution_planner_node

# Pre-orchestration Retrieval layer
from agents.nodes.retrieval_manager import retrieval_manager_node
from agents.nodes.knowledge_gateway import knowledge_gateway_node
from agents.nodes.compare_router import compare_router_node
from agents.rag import has_documents

# Fast Path
from agents.nodes.fast_search_agent import fast_search_agent_node

# Orchestration & Domain Agents
from agents.nodes.orchestrator import orchestrator
from agents.nodes.live_score_agent import live_score_agent_node
from agents.nodes.news_agent import news_agent_node
from agents.nodes.finance_agent import finance_agent_node
from agents.nodes.shopping_agent import shopping_agent_node
from agents.nodes.coding_agent import coding_agent_node
from agents.nodes.generic_agent import generic_agent_node

# Evidence Pipeline
from agents.nodes.url_deduplicator import url_deduplicator_node
from agents.nodes.page_fetcher import page_fetcher_node
from agents.nodes.chunking_engine import chunking_engine_node
from agents.nodes.reranker import reranker_node
from agents.nodes.synthesizer import synthesizer_node
from agents.nodes.evidence_verifier import evidence_verifier_node
from agents.nodes.critic import critic_node

# Verification & Citation
from agents.nodes.citation_formatter import citation_formatter_node
from agents.nodes.fact_checker import fact_checker_node

# Response
from agents.nodes.report import response_composer_node
from agents.nodes.markdown_renderer import markdown_renderer_node

# Memory
from memory import chat_store, summary_store, context_assembler
from agents.rag import retrieve_with_hyde

# ============================================================
# Constants
# ============================================================

MAX_ITERATIONS = 2

# ============================================================
# Helper Nodes
# ============================================================

def finalize(state: FINALSTATE):
    """Terminal node — packs the final markdown into the messages list."""
    report = state.get("final_report", "")
    content = report if isinstance(report, str) else str(report)
    return {"messages": [("assistant", content)]}

async def context_assembly_node(state: FINALSTATE):
    """
    Assembles all memory sources into a single context block.
    Runs before response_composer. Merges: conversation summary, recent turns,
    semantic memory, RAG doc chunks, and web evidence.
    """
    thread_id = state.get("_thread_id", "")
    query_route = state.get("query_router_output")
    route = query_route.route if query_route else "web_only"

    # Gather doc chunks based on route OR if retrieval_manager produced output
    doc_chunks = []
    rm_out = state.get("retrieval_manager_output")
    
    if rm_out and rm_out.pdf_contexts:
        doc_chunks = rm_out.pdf_contexts
    elif route in ("docs_only", "docs_and_web"):
        # Try HyDE retrieval directly as fallback
        try:
            doc_chunks = await retrieve_with_hyde(state.get("user_query", ""), k=5)
        except Exception:
            pass

    # Gather web evidence
    web_context = ""
    if route in ("web_only", "docs_and_web"):
        web_context = state.get("synthesized_context", "")
        if not web_context:
            web_context = state.get("fetched_content", "")

    # For conversation_only route, we don't need doc or web chunks
    assembled = context_assembler.assemble_context(
        thread_id=thread_id,
        doc_chunks=doc_chunks if route != "conversation_only" else [],
        web_context=web_context if route != "conversation_only" else "",
    )

    print(f"Context Assembly: Merged {len(assembled)} chars of context (route={route})")
    return {"assembled_context": assembled}

# ============================================================
# Routing Functions
# ============================================================

def route_start(state: FINALSTATE):
    """Route from START: Always go to query_rewriter first for coreference resolution."""
    return "query_rewriter"

def route_after_rewriter(state: FINALSTATE):
    """After query rewriting, check if documents exist for local RAG."""
    if has_documents():
        return "retrieval_manager"
    return "intent_router"

def route_compare_router(state: FINALSTATE):
    """After compare router, decide to go to intent_router or skip directly to context_assembly."""
    out = state.get("compare_router_output")
    if out and out.needs_web_search:
        return "intent_router"
    return "context_assembly"

def route_intent(state: FINALSTATE):
    """Route based on the UI toggle: simple -> fast_search, complex -> semantic pipeline."""
    if state["intent_output"].intent == "simple":
        return "fast_search"
    return "query_analyzer"

def route_after_query_router(state: FINALSTATE):
    """After query router decides retrieval source, route accordingly."""
    qr = state.get("query_router_output")
    if not qr:
        return "knowledge_gateway"  # fallback

    if qr.route == "no_retrieval":
        return "context_assembly"
    elif qr.route == "conversation_only":
        return "context_assembly"
    elif qr.route == "docs_only":
        return "knowledge_gateway"
    else:
        # web_only or docs_and_web — go through the full orchestrator pipeline
        return "knowledge_gateway"

def route_after_execution_planner(state: FINALSTATE):
    """After Execution Planner, go to query_router for source selection."""
    return "query_router"

from langgraph.types import Send

def route_orchestrator(state: FINALSTATE):
    """Route orchestrator assignments to domain agents via capability mapping."""
    assignments = state["decompose_tasks"].assignments
    if not assignments:
        return "url_deduplicator"

    sends = []
    for assignment in assignments:
        agent_name = CAPABILITY_TO_AGENT.get(assignment.capability, "general_agent")
        sends.append(Send(agent_name, {"assignment": assignment}))
    return sends

def route_after_critic(state: FINALSTATE):
    """After the critic, decide if we need another round or proceed to verification."""
    if state["critic_output"].needs_more_research and state["iteration_count"] < MAX_ITERATIONS:
        if "execution_strategy" not in state or not state["execution_strategy"]:
            return "intent_router"
        return "orchestrator"
    return "evidence_verifier"

# ============================================================
# Build the Graph
# ============================================================

builder = StateGraph(FINALSTATE)

# --- Register All Nodes ---

# Memory-aware Query Intelligence
builder.add_node("query_rewriter", query_rewriter_node)
builder.add_node("query_router", query_router_node)
builder.add_node("context_assembly", context_assembly_node)

# Semantic Pipeline
builder.add_node("intent_router", intent_router_node)
builder.add_node("query_analyzer", query_analyzer_node)
builder.add_node("knowledge_analyzer", knowledge_analyzer_node)
builder.add_node("answer_contract_builder", answer_contract_builder_node)
builder.add_node("execution_planner", execution_planner_node)

# Retrieval Layer
builder.add_node("retrieval_manager", retrieval_manager_node)
builder.add_node("compare_router", compare_router_node)
builder.add_node("knowledge_gateway", knowledge_gateway_node)

# Fast Path
builder.add_node("fast_search", fast_search_agent_node)

# Orchestrator
builder.add_node("orchestrator", orchestrator)

# Domain Agents
DOMAIN_AGENTS = [
    "live_score_agent", "news_agent", "finance_agent",
    "shopping_agent", "coding_agent", "general_agent"
]
builder.add_node("live_score_agent", live_score_agent_node)
builder.add_node("news_agent", news_agent_node)
builder.add_node("finance_agent", finance_agent_node)
builder.add_node("shopping_agent", shopping_agent_node)
builder.add_node("coding_agent", coding_agent_node)
builder.add_node("general_agent", generic_agent_node)

# Evidence Pipeline
builder.add_node("url_deduplicator", url_deduplicator_node)
builder.add_node("page_fetcher", page_fetcher_node)
builder.add_node("chunking_engine", chunking_engine_node)
builder.add_node("reranker", reranker_node)
builder.add_node("synthesizer", synthesizer_node)
builder.add_node("critics", critic_node)
builder.add_node("evidence_verifier", evidence_verifier_node)

# Verification & Citation
builder.add_node("citations", citation_formatter_node)
builder.add_node("fact_checks", fact_checker_node)

# Response
builder.add_node("response_composer", response_composer_node)
builder.add_node("markdown_renderer", markdown_renderer_node)
builder.add_node("finalize", finalize)

# ============================================================
# Wire the Edges
# ============================================================

# Entry: START -> query_rewriter (always)
builder.add_conditional_edges(START, route_start, {
    "query_rewriter": "query_rewriter"
})

# After rewriter: check if docs exist -> RAG path or intent_router
builder.add_conditional_edges("query_rewriter", route_after_rewriter, {
    "retrieval_manager": "retrieval_manager",
    "intent_router": "intent_router"
})

# RAG Layer
builder.add_edge("retrieval_manager", "compare_router")
builder.add_conditional_edges("compare_router", route_compare_router, {
    "intent_router": "intent_router",
    "context_assembly": "context_assembly"
})

# Intent Router: simple -> fast_search, complex -> semantic pipeline
builder.add_conditional_edges("intent_router", route_intent, {
    "fast_search": "fast_search",
    "query_analyzer": "query_analyzer"
})
builder.add_edge("fast_search", "finalize")

# Semantic Pipeline (linear chain)
builder.add_edge("query_analyzer", "knowledge_analyzer")
builder.add_edge("knowledge_analyzer", "answer_contract_builder")
builder.add_edge("answer_contract_builder", "execution_planner")

# Execution Planner -> Query Router (source selection)
builder.add_conditional_edges("execution_planner", route_after_execution_planner, {
    "query_router": "query_router"
})

# Query Router -> route based on retrieval source
builder.add_conditional_edges("query_router", route_after_query_router, {
    "context_assembly": "context_assembly",
    "knowledge_gateway": "knowledge_gateway",
})

builder.add_edge("knowledge_gateway", "orchestrator")

# Orchestrator -> Domain Agents (parallel via Send)
builder.add_conditional_edges("orchestrator", route_orchestrator, DOMAIN_AGENTS + ["url_deduplicator"])

# Domain Agents -> URL Deduplicator (all converge)
for agent in DOMAIN_AGENTS:
    builder.add_edge(agent, "url_deduplicator")

# Evidence Pipeline (linear chain)
builder.add_edge("url_deduplicator", "page_fetcher")
builder.add_edge("page_fetcher", "chunking_engine")
builder.add_edge("chunking_engine", "reranker")
builder.add_edge("reranker", "synthesizer")
builder.add_edge("synthesizer", "critics")

# Critic Loop
builder.add_conditional_edges("critics", route_after_critic, {
    "intent_router": "intent_router",
    "orchestrator": "orchestrator",
    "evidence_verifier": "evidence_verifier"
})

# Post-Evidence Pipeline
builder.add_edge("evidence_verifier", "citations")
builder.add_edge("citations", "fact_checks")
builder.add_edge("fact_checks", "context_assembly")

# Context Assembly -> Response Composer
builder.add_edge("context_assembly", "response_composer")

# Response Pipeline
builder.add_edge("response_composer", "markdown_renderer")
builder.add_edge("markdown_renderer", "finalize")

# Terminal
builder.add_edge("finalize", END)

# ============================================================
# Compile
# ============================================================

graph = builder.compile()

def set_checkpointer(checkpointer):
    global graph
    graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# API Entry Points
# ============================================================

async def process_message_with_agents(message: str, thread_id: str = None) -> str:
    """Entry point for the API to call the LangGraph."""
    try:
        import uuid
        actual_thread_id = thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": actual_thread_id}, "recursion_limit": 100}
        result = await graph.ainvoke({
            "user_query": message,
            "messages": [("user", message)],
            "iteration_count": 0,
            "_thread_id": actual_thread_id,
        }, config=config)

        report = result.get("final_report", "")
        return report if report else "Task completed, but no report was generated."
    except Exception as e:
        return f"An error occurred during swarm processing: {str(e)}"

import json
import time as time_module
import asyncio

async def stream_message_with_agents(message: str, mode: str = "simple", thread_id: str = None):
    node_start_times = {}

    async def run_and_stream():
        try:
            import uuid
            actual_thread_id = thread_id or str(uuid.uuid4())

            # Save user turn BEFORE graph execution
            chat_store.add_turn(actual_thread_id, "user", message, mode)

            config = {"configurable": {"thread_id": actual_thread_id}, "recursion_limit": 100}
            async for event in graph.astream_events(
                {
                    "user_query": message,
                    "messages": [("user", message)],
                    "search_mode": mode,
                    "iteration_count": 0,
                    "_thread_id": actual_thread_id,
                },
                config=config,
                version="v2"
            ):
                kind = event.get("event", "")
                node_name = event.get("name", "")

                # Known set of our real graph nodes — only emit events for these
                VALID_NODES = {
                    "query_rewriter", "query_router", "context_assembly",
                    "intent_router", "fast_search",
                    "query_analyzer", "knowledge_analyzer",
                    "answer_contract_builder", "execution_planner",
                    "orchestrator",
                    "url_deduplicator", "page_fetcher", "chunking_engine", "reranker", "synthesizer",
                    "critics", "evidence_verifier", "citations",
                    "fact_checks", "response_composer", "markdown_renderer", "finalize",
                    "live_score_agent", "news_agent", "finance_agent",
                    "shopping_agent", "coding_agent", "general_agent",
                    "retrieval_manager", "compare_router", "knowledge_gateway"
                }

                if node_name not in VALID_NODES:
                    continue

                if kind == "on_chain_start":
                    node_start_times[node_name] = time_module.time()
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name})}\n\n"

                elif kind == "on_chain_end":
                    start_t = node_start_times.get(node_name, time_module.time())
                    elapsed = round(time_module.time() - start_t, 1)
                    output = event.get("data", {}).get("output", {}) or {}

                    data = {
                        "type": "agent_update",
                        "node": node_name,
                        "time_taken": elapsed,
                        "status": "done"
                    }

                    # Generic extraction for frontend (clickable details)
                    if isinstance(output, dict):
                        filtered = {}
                        ignore_keys = {"messages", "final_report", "fetched_content", "synthesized_context", "sources", "chunks", "assembled_context"}
                        def _make_serializable(obj):
                            if hasattr(obj, 'model_dump'):
                                return obj.model_dump()
                            elif hasattr(obj, 'dict'):
                                return obj.dict()
                            elif isinstance(obj, list):
                                return [_make_serializable(i) for i in obj]
                            elif isinstance(obj, dict):
                                return {k: _make_serializable(v) for k, v in obj.items()}
                            elif isinstance(obj, (str, int, float, bool, type(None))):
                                return obj
                            else:
                                return str(obj)

                        for k, v in output.items():
                            if k not in ignore_keys:
                                filtered[k] = _make_serializable(v)
                        if filtered:
                            if len(filtered) == 1:
                                data["node_output"] = list(filtered.values())[0]
                            else:
                                data["node_output"] = filtered

                    # Extract final report (markdown) from markdown_renderer
                    if isinstance(output, dict) and "final_report" in output:
                        report = output["final_report"]
                        content = report if isinstance(report, str) else str(report)
                        if content:
                            data["content"] = content

                            # Save assistant turn AFTER getting the report
                            chat_store.add_turn(actual_thread_id, "assistant", content[:500], mode)

                            # Trigger summary update if needed (async, non-blocking)
                            turn_count = chat_store.get_turn_count(actual_thread_id)
                            if summary_store.should_update(actual_thread_id, turn_count):
                                all_turns = chat_store.get_all_turns(actual_thread_id)
                                asyncio.create_task(
                                    summary_store.generate_and_update(actual_thread_id, all_turns, turn_count)
                                )

                    # Extract claims from fact_checks
                    if isinstance(output, dict) and "fact_checker" in output:
                        claims = getattr(output["fact_checker"], "verified_claims", [])
                        data["claims"] = [
                            {
                                "claim": getattr(c, "claim", ""),
                                "trust_score": getattr(c, "trust_score", 0),
                                "citations": getattr(c, "citations", [])
                            }
                            for c in claims
                        ]

                    yield f"data: {json.dumps(data)}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    q = asyncio.Queue()

    async def producer():
        try:
            async for chunk in run_and_stream():
                await q.put(chunk)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await q.put(f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
        finally:
            await q.put(None)

    task = asyncio.create_task(producer())

    try:
        while True:
            try:
                chunk = await asyncio.wait_for(q.get(), timeout=15.0)
                if chunk is None:
                    break
                yield chunk
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    finally:
        task.cancel()
