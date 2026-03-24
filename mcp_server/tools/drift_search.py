from core.data_loader import load_all
from core.llm_factory import get_llm, get_text_embedder
from core.search import run_drift_search

async def drift_search_tool(
    query: str,
    community_level: int = 2,
    response_type: str = "Multiple Paragraphs",
) -> dict:
    data = load_all()
    return await run_drift_search(
        query,
        data=data,
        llm=get_llm(),
        text_embedder=get_text_embedder(),
        community_level=community_level,
        response_type=response_type,
    )
