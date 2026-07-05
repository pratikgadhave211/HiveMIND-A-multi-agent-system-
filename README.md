# HiveMIND: A Multi-Agent System

HiveMIND (Deep Agent Swarm) is an advanced, highly-orchestrated multi-agent architecture built with **LangGraph**, **FastAPI**, **React**, and **PostgreSQL**. It breaks down complex queries, routes them to specialized domain agents, retrieves real-time data, and synthesizes highly accurate, fact-checked, and cited responses.

## 🌟 Key Features

- **Multi-Agent Orchestration**: Specialized agents for Finance, News, Live Scores, Shopping, Coding, and General inquiries.
- **Advanced Query Intelligence**: 
  - *Query Rewriting & Routing*: Intelligently resolves coreferences and routes between fast search and complex semantic pipelines.
  - *Knowledge Gateway*: Merges local documents (RAG) with web search.
- **Evidence & Verification Pipeline**:
  - URL Deduplication, Page Fetching, Chunking, and Reranking.
  - Built-in **Critic** and **Evidence Verifier** to ensure accuracy before finalizing reports.
  - Fact-checking and automated citation formatting.
- **Stateful Memory**: Postgres-backed memory stores for chat history, summaries, and semantic context across conversations.
- **Modern Frontend**: React + Vite UI with Tailwind CSS and Framer Motion for a dynamic, real-time streaming agent visualization.

## 🏗️ Architecture

- **Backend**: Python, FastAPI, LangGraph, LangChain, PostgreSQL (Checkpointer).
- **Frontend**: React 19, Vite, Tailwind CSS 4, Framer Motion, React Flow.
- **Infrastructure**: Docker & Docker Compose for easy deployment.

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- API Keys for OpenAI / Tavily / NVIDIA (depending on your `.env` configuration)
- Node.js & npm (for frontend)

### 1. Environment Setup

Create a `.env` file in the root directory (or in `./backend`) and add your API keys:
```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
NVIDIA_API_KEY=your_nvidia_key
```

### 2. Run with Docker Compose

Start the Postgres database and backend API:
```bash
docker-compose up --build -d
```
The backend API will be available at `http://localhost:8000`.

### 3. Start the Frontend

Navigate to the `frontend` directory, install dependencies, and start the development server:
```bash
cd frontend
npm install
npm run dev
```
The frontend UI will typically be available at `http://localhost:5173`.

## 🧠 Core Agent Workflow
1. **Query Rewriter & Router**: Processes user intent and determines if local RAG or Web Search is needed.
2. **Intent Router**: Chooses between a "fast path" or a deep "semantic pipeline".
3. **Execution Planner**: Decomposes complex tasks and assigns them to Domain Agents.
4. **Domain Agents**: Fetch specific context (Finance, News, Code, etc.).
5. **Evidence Pipeline**: Synthesizes the data, runs it through a critic, and verifies facts.
6. **Markdown Renderer**: Formats the final cited report for the user.

## 📄 License
This project is open-source and available under the MIT License.
