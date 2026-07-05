from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import sys
import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from agents.workflow import set_checkpointer
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from api.testing_routes import router as testing_router

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup PostgreSQL connection pool
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/langgraph_db")
    async with AsyncConnectionPool(
        conninfo=db_url,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    ) as pool:
        serde = JsonPlusSerializer(allowed_msgpack_modules=[
            ('agents.state', 'PlannerOutput'),
            ('agents.state', 'ExecutionStrategy'),
            ('agents.state', 'RetrievalManagerOutput'),
            ('agents.state', 'KnowledgeGatewayOutput'),
            ('agents.state', 'OrchestratorOutput'),
            ('agents.state', 'CriticOutput'),
            ('agents.state', 'CompareRouterOutput'),
            ('agents.state', 'QueryAnalysis'),
            ('agents.state', 'KnowledgeAnalysis'),
            ('agents.state', 'VerificationStrategy'),
            ('agents.state', 'AnswerContract'),
            ('agents.state', 'Assignment'),
            ('agents.state', 'Source'),
            ('agents.state', 'SearchResult'),
            ('agents.state', 'TrustDimensions'),
            ('agents.state', 'VerifiedClaim'),
            ('agents.state', 'IntentOutput'),
            ('agents.state', 'FactCheckOutput'),
            ('agents.state', 'Chunk'),
            ('agents.state', 'ReportSection'),
            ('agents.state', 'StructuredResponse'),
            ('agents.state', 'FinalReport'),
            ('agents.state', 'QueryRewriterOutput'),
            ('agents.state', 'QueryRouterOutput'),
        ])
        checkpointer = AsyncPostgresSaver(pool, serde=serde)
        
        # We need to setup the checkpointer tables (this is synchronous in AsyncPostgresSaver in current versions)
        # However, AsyncPostgresSaver has an async setup() method.
        await checkpointer.setup()
        
        # Inject the checkpointer into the workflow
        set_checkpointer(checkpointer)
        
        yield
    
app = FastAPI(title="Deep Agent Swarm API", lifespan=lifespan)

# Configure CORS so the frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(testing_router, prefix="/api/test", tags=["Node Testing"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Deep Agent Swarm API"}
