from fastapi import APIRouter
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from agents.nodes.intent_router import intent_router_node
from agents.nodes.fast_search_agent import fast_search_agent_node
from agents.nodes.query_analyzer import query_analyzer_node
from agents.nodes.knowledge_analyzer import knowledge_analyzer_node
from agents.nodes.planner import answer_contract_builder_node
from agents.nodes.execution_planner import execution_planner_node
from agents.nodes.orchestrator import orchestrator
from agents.nodes.generic_agent import generic_agent_node
from agents.nodes.url_deduplicator import url_deduplicator_node
from agents.nodes.page_fetcher import page_fetcher_node
from agents.nodes.chunking_engine import chunking_engine_node
from agents.nodes.reranker import reranker_node
from agents.nodes.synthesizer import synthesizer_node
from agents.nodes.critic import critic_node
from agents.nodes.evidence_verifier import evidence_verifier_node
from agents.nodes.report import response_composer_node
from agents.nodes.markdown_renderer import markdown_renderer_node

router = APIRouter()

class NodeTestRequest(BaseModel):
    user_query: Optional[str] = ""
    search_mode: Optional[str] = "simple"
    fetched_content: Optional[str] = ""
    synthesized_context: Optional[str] = ""
    sources: Optional[List[Dict[str, Any]]] = []
    deduped_sources: Optional[List[Dict[str, Any]]] = []
    chunks: Optional[List[Dict[str, Any]]] = []
    reranked_chunks: Optional[List[Dict[str, Any]]] = []
    iteration_count: Optional[int] = 0
    assignment: Optional[Dict[str, Any]] = None
    initial_search_context: Optional[str] = ""

    class Config:
        extra = "allow"

def to_state(req: NodeTestRequest) -> dict:
    return req.model_dump(exclude_none=True)

@router.post("/intent_router")
async def test_intent_router(request: NodeTestRequest):
    return await intent_router_node(to_state(request))

@router.post("/fast_search")
async def test_fast_search(request: NodeTestRequest):
    return await fast_search_agent_node(to_state(request))

@router.post("/query_analyzer")
async def test_query_analyzer(request: NodeTestRequest):
    return await query_analyzer_node(to_state(request))

@router.post("/knowledge_analyzer")
async def test_knowledge_analyzer(request: NodeTestRequest):
    return await knowledge_analyzer_node(to_state(request))

@router.post("/answer_contract_builder")
async def test_answer_contract(request: NodeTestRequest):
    return await answer_contract_builder_node(to_state(request))

@router.post("/execution_planner")
async def test_execution_planner(request: NodeTestRequest):
    return await execution_planner_node(to_state(request))

@router.post("/orchestrator")
async def test_orchestrator(request: NodeTestRequest):
    return await orchestrator(to_state(request))

@router.post("/generic_agent")
async def test_generic_agent(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Assignment
    if "assignment" in state_dict and isinstance(state_dict["assignment"], dict):
        state_dict["assignment"] = Assignment.model_validate(state_dict["assignment"])
    return await generic_agent_node(state_dict)

@router.post("/url_deduplicator")
async def test_url_deduplicator(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Source
    if "sources" in state_dict:
        state_dict["sources"] = [Source.model_validate(s) if isinstance(s, dict) else s for s in state_dict["sources"]]
    return await url_deduplicator_node(state_dict)

@router.post("/page_fetcher")
async def test_page_fetcher(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Source
    for key in ["deduped_sources", "sources"]:
        if key in state_dict:
            state_dict[key] = [Source.model_validate(s) if isinstance(s, dict) else s for s in state_dict[key]]
    return await page_fetcher_node(state_dict)

@router.post("/chunking_engine")
async def test_chunking_engine(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Source
    if "deduped_sources" in state_dict:
        state_dict["deduped_sources"] = [Source.model_validate(s) if isinstance(s, dict) else s for s in state_dict["deduped_sources"]]
    return await chunking_engine_node(state_dict)

@router.post("/reranker")
async def test_reranker(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Chunk
    if "chunks" in state_dict:
        state_dict["chunks"] = [Chunk.model_validate(c) if isinstance(c, dict) else c for c in state_dict["chunks"]]
    return await reranker_node(state_dict)

@router.post("/synthesizer")
async def test_synthesizer(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Chunk
    if "reranked_chunks" in state_dict:
        state_dict["reranked_chunks"] = [Chunk.model_validate(c) if isinstance(c, dict) else c for c in state_dict["reranked_chunks"]]
    return await synthesizer_node(state_dict)

@router.post("/critics")
async def test_critics(request: NodeTestRequest):
    return await critic_node(to_state(request))

@router.post("/evidence_verifier")
async def test_evidence_verifier(request: NodeTestRequest):
    state_dict = to_state(request)
    from agents.state import Source
    if "sources" in state_dict:
        state_dict["sources"] = [Source.model_validate(s) if isinstance(s, dict) else s for s in state_dict["sources"]]
    return await evidence_verifier_node(state_dict)

@router.post("/response_composer")
async def test_response_composer(request: NodeTestRequest):
    return await response_composer_node(to_state(request))

@router.post("/markdown_renderer")
async def test_markdown_renderer(request: NodeTestRequest):
    return await markdown_renderer_node(to_state(request))
