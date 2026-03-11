"""
One-shot script: reads GraphRAG Parquet output and populates Qdrant.
Run once after `graphrag index --root .`
"""
import asyncio
import openai
from core.config import settings
from core.data_loader import load_all
from core.vector_store import get_client as get_qdrant, ensure_collection, upsert_chunks

BATCH_SIZE = 100

async def embed_texts(texts: list[str]) -> list[list[float]]:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        response = await client.embeddings.create(
            input=batch,
            model="text-embedding-3-small",
        )
        embeddings.extend([r.embedding for r in response.data])
        print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
    return embeddings

async def populate_qdrant(data):
    print("Populating Qdrant...")
    qdrant = get_qdrant()
    ensure_collection(qdrant, vector_size=1536)

    # Build chunks from text_units — attach entity_ids for graph seed extraction
    chunks = []
    for _, row in data.text_units.iterrows():
        chunks.append({
            "id": str(row["id"]),
            "text": str(row.get("text", "")),
            "doc_title": str(row.get("document_ids", ["unknown"])[0])
                         if isinstance(row.get("document_ids"), list) else "unknown",
            "entity_ids": [str(eid) for eid in row.get("entity_ids", [])]
                          if isinstance(row.get("entity_ids"), list) else [],
        })

    texts = [c["text"] for c in chunks]
    embeddings = await embed_texts(texts)
    upsert_chunks(qdrant, chunks, embeddings)
    print(f"  Upserted {len(chunks)} chunks into Qdrant.")

async def main():
    data = load_all()
    await populate_qdrant(data)
    print("Done. Qdrant store is ready.")

if __name__ == "__main__":
    asyncio.run(main())
