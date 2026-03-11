from core.data_loader import load_all
from core.bm25_index import BM25Index
from core.hybrid_search import hybrid_search

# BM25 index and data built once at first request, then cached
_bm25_cache: BM25Index | None = None
_data_cache = None

def _get_bm25_and_data():
    global _bm25_cache, _data_cache
    if _bm25_cache is None:
        _data_cache = load_all()
        cols = ["id", "text"] + (
            ["entity_ids"] if "entity_ids" in _data_cache.text_units.columns else []
        )
        chunks = _data_cache.text_units[cols].to_dict("records")
        _bm25_cache = BM25Index(chunks)
    return _bm25_cache, _data_cache

async def hybrid_search_tool(
    query: str,
    query_vector: list[float],
    top_k: int = 10,
    graph_hops: int = 2,
) -> dict:
    bm25, data = _get_bm25_and_data()
    results = hybrid_search(query, query_vector, bm25, top_k=top_k, graph_hops=graph_hops, data=data)
    return {
        "query": query,
        "results": results,
        "layers_used": ["vector", "bm25", "graph"],
        "total": len(results),
    }
