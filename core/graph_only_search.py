"""
Lightweight search using only BM25 + Pandas graph expansion.
No vector embeddings required. Useful for testing and low-resource environments.
"""
from collections import defaultdict
from core.bm25_index import BM25Index
from core.graph_store import graph_expand
from core.data_loader import GraphData

RRF_K = 60

def _rrf_score(rank: int) -> float:
    return 1.0 / (RRF_K + rank)

def graph_only_search(
    query: str,
    bm25_index: BM25Index,
    data: GraphData,
    top_k: int = 10,
    graph_hops: int = 2,
) -> list[dict]:
    scores: dict[str, float] = defaultdict(float)
    payloads: dict[str, dict] = {}

    # Layer 1: BM25 full-text on text_units
    for rank, (chunk, score) in enumerate(bm25_index.search(query, top_k=top_k)):
        cid = chunk["id"]
        scores[cid] += _rrf_score(rank)
        payloads[cid] = chunk

    # Layer 2: graph expansion from top-scoring chunks' entity seeds
    top_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    seed_entities = []
    for cid, _ in top_chunks:
        seed_entities.extend(payloads[cid].get("entity_ids", []))
    seed_entities = list(set(seed_entities))

    if seed_entities:
        nodes = graph_expand(data, seed_entities, hops=graph_hops)
        for rank, node in enumerate(nodes):
            node_id = f"graph::{node['title']}"
            scores[node_id] += _rrf_score(rank)
            payloads[node_id] = {
                "id": node_id,
                "text": node.get("description", ""),
                "doc_title": "knowledge_graph",
                "source": "graph",
                "entity_ids": [],
            }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"score": score, **payloads[cid]} for cid, score in ranked if cid in payloads]
