from core.data_loader import load_all
from core.llm_factory import get_llm
from core.search import run_global_search

async def global_search_tool(query: str) -> dict:
    data = load_all()
    return await run_global_search(query, data=data, llm=get_llm())
