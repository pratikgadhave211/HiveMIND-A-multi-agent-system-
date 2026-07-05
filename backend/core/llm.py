import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from tavily import TavilyClient

load_dotenv()

# API key is securely loaded from .env via load_dotenv()
if not os.environ.get("NVIDIA_API_KEY"):
    print("Warning: NVIDIA_API_KEY not found in environment.")

# Planner / Orchestrator / Fast Search
llm = ChatNVIDIA(
    model="qwen/qwen3-next-80b-a3b-instruct",
    temperature=1,
)

# Critic / Fact Checker / Verifier
model = ChatNVIDIA(
    model="deepseek-ai/deepseek-v4-pro",
    temperature=1,
)

# Synthesizer / Final Report Generator
generate_model = ChatNVIDIA(
    model="qwen/qwen3.5-122b-a10b",
    temperature=0.7,
)

# Backup Model
backup_model = ChatNVIDIA(
    model="meta/llama-3.1-8b-instruct",
    temperature=0.2,
)

# Backup Critic / Generator
backup2criticandgenerate_model = ChatNVIDIA(
    model="meta/llama-3.3-70b-instruct",
    temperature=0.5,
)

# Playwright Browser Agent LLM
playwright_llm = ChatNVIDIA(
    model="meta/llama-3.1-8b-instruct",
    temperature=0.3,
)

# Tavily
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)
