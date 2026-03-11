from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from core.bm25_index import BM25Index
from core.graph_store import graph_expand
from core.config import settings

RRF_K = 60  # standard Reciprocal Rank Fusion constant

def _rrf_score(rank: int) -> float:
    return 1.0 / (RRF_K + rank)

def _get_lancedb_store() -> LanceDBVectorStore:
    store = LanceDBVectorStore(vector_store_schema_config=VectorStoreSchemaConfig())
    store.index_name = "default-text_unit-text"
    store.connect(db_uri=str(Path(settings.graphrag_output_dir) / "lancedb"))
    return store

def hybrid_search(
    query: str,
    query_vector: list[float],
    bm25_index: BM25Index,
    top_k: int = 10,
    graph_hops: int = 2,
    data=None,
) -> list[dict]:
    scores: dict[str, float] = defaultdict(float)
    payloads: dict[str, dict] = {}

    # Layer 1: vector similarity via LanceDB
    store = _get_lancedb_store()
    for rank, result in enumerate(store.similarity_search_by_vector(query_vector, k=top_k)):
        doc = result.document
        cid = doc.id
        scores[cid] += _rrf_score(rank)
        attrs = doc.attributes or {}
        doc_ids = attrs.get("document_ids", ["unknown"])
        payloads[cid] = {
            "id": cid,
            "text": doc.text or "",
            "doc_title": doc_ids[0] if isinstance(doc_ids, list) else "unknown",
            "entity_ids": attrs.get("entity_ids", []),
            "source": "vector",
        }

    # Layer 2: BM25 full-text — good for exact terms/codes
    for rank, (chunk, _) in enumerate(bm25_index.search(query, top_k=top_k)):
        cid = chunk["id"]
        scores[cid] += _rrf_score(rank)
        payloads[cid] = chunk

    # Layer 3: Pandas graph expansion from top-scored entity seeds
    seeds = _extract_seed_entities(payloads, scores, n=5)
    if seeds and data is not None:
        for rank, node in enumerate(graph_expand(data, seeds, hops=graph_hops)):
            node_id = f"graph::{node['title']}"
            scores[node_id] += _rrf_score(rank)
            payloads[node_id] = {
                "id": node_id,
                "text": node.get("description", ""),
                "doc_title": "knowledge_graph",
                "source": "graph",
            }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"score": score, **payloads[cid]} for cid, score in ranked if cid in payloads]

def _extract_seed_entities(payloads: dict, scores: dict, n: int) -> list[str]:
    top = sorted(
        [(cid, s) for cid, s in scores.items() if not cid.startswith("graph::")],
        key=lambda x: x[1], reverse=True,
    )[:n]
    entities = []
    for cid, _ in top:
        entities.extend(payloads.get(cid, {}).get("entity_ids", []))
    return list(set(entities))
