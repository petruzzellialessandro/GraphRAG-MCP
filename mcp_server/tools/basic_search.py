from core.data_loader import load_all
from core.llm_factory import get_llm, get_text_embedder
from core.search import run_local_search


async def basic_search_tool(
    query: str,
    response_type: str = "Multiple Paragraphs",
) -> dict:
    """Baseline GraphRAG search (standard RAG path)."""
    data = load_all()
    result = await run_local_search(
        query,
        data=data,
        llm=get_llm(),
        text_embedder=get_text_embedder(),
        community_level=2,
        response_type=response_type,
    )
    result["search_type"] = "basic"
    return result
