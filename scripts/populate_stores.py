"""
Verification script: checks that all GraphRAG data stores are accessible.
LanceDB vector stores are populated automatically by `graphrag index`.
Run this after indexing to confirm everything is in order.
"""
import asyncio
from pathlib import Path
from core.config import settings
from core.data_loader import load_all
from graphrag.vector_stores.lancedb import LanceDBVectorStore
from graphrag.config.models.vector_store_schema_config import VectorStoreSchemaConfig


def _check_lancedb_store(index_name: str) -> int:
    store = LanceDBVectorStore(vector_store_schema_config=VectorStoreSchemaConfig())
    store.index_name = index_name
    store.connect(db_uri=str(Path(settings.graphrag_output_dir) / "lancedb"))
    count = store.document_collection.count_rows()
    print(f"  {index_name}: {count} rows")
    return count


async def main():
    print("Checking GraphRAG data stores...")

    data = load_all()
    print(f"  Entities: {len(data.entities)}")
    print(f"  Relationships: {len(data.relationships)}")
    print(f"  Text units: {len(data.text_units)}")
    print(f"  Communities: {len(data.communities)}")
    print(f"  Community reports: {len(data.community_reports)}")

    print("\nChecking LanceDB vector stores...")
    for table in ("default-entity-description", "default-text_unit-text"):
        _check_lancedb_store(table)

    print("\nAll stores OK.")


if __name__ == "__main__":
    asyncio.run(main())
