"""
Unified search interface for GraphRAG v2.7+.
Uses GlobalSearch / LocalSearch with the proper context builders.
"""
from core.data_loader import GraphData
from core.source_resolver import resolve_sources
from graphrag.query.indexer_adapters import (
    read_indexer_entities,
    read_indexer_communities,
    read_indexer_reports,
    read_indexer_relationships,
    read_indexer_text_units,
)
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig
from core.config import settings
from pathlib import Path


def _entity_description_store(data: GraphData):
    """Open the LanceDB entity-description vector store produced by the indexer."""
    schema_config = VectorStoreSchemaConfig()
    store = LanceDBVectorStore(vector_store_schema_config=schema_config)
    store.index_name = "default-entity-description"
    store.connect(db_uri=str(Path(settings.graphrag_output_dir) / "lancedb"))
    return store


async def run_local_search(
    query: str,
    data: GraphData,
    llm,
    text_embedder,
    community_level: int = 2,
    response_type: str = "Multiple Paragraphs",
) -> dict:
    entities = read_indexer_entities(data.entities, data.communities, community_level)
    relationships = read_indexer_relationships(data.relationships)
    reports = read_indexer_reports(data.community_reports, data.communities, community_level)
    text_units = read_indexer_text_units(data.text_units)
    description_store = _entity_description_store(data)

    context_builder = LocalSearchMixedContext(
        entities=entities,
        relationships=relationships,
        community_reports=reports,
        text_units=text_units,
        entity_text_embeddings=description_store,
        text_embedder=text_embedder,
    )
    engine = LocalSearch(
        model=llm,
        context_builder=context_builder,
        response_type=response_type,
    )
    result = await engine.search(query)
    ctx = result.context_data if isinstance(result.context_data, dict) else {}
    resolved = resolve_sources(ctx.get("sources"), data)
    return {
        "answer": result.response,
        "context": {
            "entities_used": len(ctx.get("entities", [])),
            "relationships_used": len(ctx.get("relationships", [])),
            "documents": list({s["document"] for s in resolved}),
        },
        "sources": resolved,
        "search_type": "local",
    }


async def run_global_search(query: str, data: GraphData, llm, community_level: int = 2) -> dict:
    reports = read_indexer_reports(data.community_reports, data.communities, community_level)
    communities = read_indexer_communities(data.communities, data.community_reports)
    entities = read_indexer_entities(data.entities, data.communities, community_level)

    context_builder = GlobalCommunityContext(
        community_reports=reports,
        communities=communities,
        entities=entities,
    )
    engine = GlobalSearch(model=llm, context_builder=context_builder)
    result = await engine.search(query)
    ctx = result.context_data if isinstance(result.context_data, dict) else {}
    return {
        "answer": result.response,
        "context": {"communities_analyzed": len(ctx.get("reports", []))},
        "search_type": "global",
    }
