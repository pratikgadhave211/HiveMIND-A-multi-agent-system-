import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from models.schemas import ChatRequest, ChatResponse
import agents.workflow as workflow
from agents.rag import process_pdf

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        chunks_count = process_pdf(tmp_path)
        
        os.remove(tmp_path)
        
        return {"message": "PDF uploaded and indexed successfully", "chunks_processed": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # This calls the LangGraph swarm workflow and returns the final report
    reply = await workflow.process_message_with_agents(request.message, request.thread_id)
    return ChatResponse(reply=reply)

@router.get("/stream")
async def stream_endpoint(message: str, mode: str = "simple", thread_id: str = None):
    return StreamingResponse(workflow.stream_message_with_agents(message, mode, thread_id), media_type="text/event-stream")

@router.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Fetches the state from the LangGraph checkpointer for the given thread."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await workflow.graph.aget_state(config)
        
        if not state or not hasattr(state, "values") or not state.values:
            return {"error": "No history found for this thread."}
            
        values = state.values
        user_query = values.get("user_query", "Unknown Query")
        final_report = values.get("final_report", "")
        if not isinstance(final_report, str):
            final_report = str(final_report)
            
        # Optional: extract claims for the UI if needed
        claims = []
        if "fact_checker" in values and hasattr(values["fact_checker"], "verified_claims"):
            claims = [
                {
                    "claim": getattr(c, "claim", ""),
                    "trust_score": getattr(c, "trust_score", 0),
                    "citations": getattr(c, "citations", [])
                }
                for c in values["fact_checker"].verified_claims
            ]
            
        return {
            "user_query": user_query,
            "final_report": final_report,
            "claims": claims
        }
    except Exception as e:
        return {"error": str(e)}
