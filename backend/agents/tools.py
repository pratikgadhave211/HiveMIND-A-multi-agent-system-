import asyncio
from langchain_core.tools import tool
import httpx
import arxiv
from agents.state import Source, SearchResult
from core.llm import tavily_client
from duckduckgo_search import DDGS

@tool
async def duckduckgo_search_tool(query: str) -> str:
    """Search the web using DuckDuckGo for general, fast, privacy-respecting queries."""
    def _search_sync():
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        sources = []
        for item in results:
            sources.append(
                Source(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    content=item.get("body", ""),
                    source_type="duckducksearch"
                )
            )
        return SearchResult(question=query, sources=sources)

    result = await asyncio.to_thread(_search_sync)
    return result.model_dump_json()

@tool
async def googlesearch_tool(query: str) -> str:
    """Search the web using Google Search for real-time data, latest news, and quick factual lookups."""
    from googlesearch import search
    def _search_sync():
        # 'search' returns an iterator of results, each is a dictionary or just URL strings depending on advanced flag
        # With advanced=True, it returns an object with url, title, description
        sources = []
        try:
            results = search(query, num_results=5, advanced=True)
            for item in results:
                sources.append(
                    Source(
                        title=getattr(item, 'title', ''),
                        url=getattr(item, 'url', ''),
                        content=getattr(item, 'description', ''),
                        source_type="googlesearch"
                    )
                )
        except Exception as e:
            print(f"    [GOOGLE SEARCH] Error: {e}")
        return SearchResult(question=query, sources=sources)

    result = await asyncio.to_thread(_search_sync)
    return result.model_dump_json()

@tool
async def github_search_tool(query: str) -> str:
    """Search GitHub repositories relevant to a research query. Returns repository names, URLs, and descriptions sorted by stars."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 5,
            },
        )
        response.raise_for_status()

    data = response.json()
    sources = [
        Source(
            title=repo["full_name"],
            url=repo["html_url"],
            content=repo.get("description") or "",
            source_type="github",
        )
        for repo in data.get("items", [])[:5]
    ]

    result = SearchResult(question=query, sources=sources)
    return result.model_dump_json()

@tool
async def tavily_search_tool(query: str, topic: str = "general", days: int = 7) -> str:
    """Search the web using Tavily for documentation, benchmarks, blog posts, product information, and general web research."""
    kwargs = {
        "query": query,
        "max_results": 5,
        "search_depth": "advanced",
        "topic": topic
    }
    if topic == "news":
        kwargs["days"] = days

    response = await asyncio.to_thread(
        tavily_client.search,
        **kwargs
    )

    sources = [
        Source(
            title=item["title"],
            url=item["url"],
            content=item["content"],
            source_type="tavily"
        )
        for item in response["results"]
    ]

    result = SearchResult(question=query, sources=sources)
    return result.model_dump_json()

@tool
async def arxiv_search_tool(query: str) -> str:
    """Search arXiv for academic papers, machine learning research, AI algorithms, and scientific publications."""
    def _search_sync():
        arxiv_client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=5
        )
        sources = []
        for paper in arxiv_client.results(search):
            sources.append(
                Source(
                    title=paper.title,
                    url=paper.entry_id,
                    content=paper.summary,
                    source_type="arxiv"
                )
            )
        return SearchResult(question=query, sources=sources)

    result = await asyncio.to_thread(_search_sync)
    return result.model_dump_json()


import os
import json

@tool
async def serper_search_tool(query: str, search_type: str = "search", tbs: str = None) -> str:
    """Search Google via Serper.dev API. Useful for Shopping, News, and General searches. search_type can be 'search', 'news', or 'shopping'."""
    from agents.state import Source, SearchResult
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("    [SERPER] API Key missing.")
        return SearchResult(question=query, sources=[]).model_dump_json()
    
    url = f"https://google.serper.dev/{search_type}"
    payload_dict = {"q": query, "num": 5}
    if tbs:
        payload_dict["tbs"] = tbs
    payload = json.dumps(payload_dict)
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, content=payload)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"    [SERPER] Error: {e}")
            return SearchResult(question=query, sources=[]).model_dump_json()

    sources = []
    items = data.get("organic", []) if search_type == "search" else data.get(search_type, [])
    # Sometimes shopping is just returned in a specific structure
    for item in items[:5]:
        sources.append(
            Source(
                title=item.get("title", ""),
                url=item.get("link", ""),
                content=item.get("snippet", ""),
                source_type=f"serper_{search_type}"
            )
        )
    return SearchResult(question=query, sources=sources).model_dump_json()

@tool
async def jina_fetch_tool(url: str) -> str:
    """Fetch clean Markdown content from a URL using Jina Reader API."""
    from agents.state import Source, SearchResult
    jina_url = f"https://r.jina.ai/{url}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(jina_url)
            response.raise_for_status()
            content = response.text
        except Exception as e:
            print(f"    [JINA] Fetch Error on {url}: {e}")
            content = ""
            
    sources = [Source(title=url, url=url, content=content[:20000], source_type="jina_extract")]
    return SearchResult(question=f"Extract {url}", sources=sources).model_dump_json()
