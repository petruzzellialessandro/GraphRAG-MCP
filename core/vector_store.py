from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from core.config import settings

COLLECTION = "graphrag_chunks"

def get_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

def ensure_collection(client: QdrantClient, vector_size: int = 1536):
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

def upsert_chunks(client: QdrantClient, chunks: list[dict], embeddings: list[list[float]]):
    # Each chunk: {"id": str, "text": str, "doc_title": str, "entity_ids": list[str]}
    # Use the chunk's own ID (as a UUID string) so Qdrant point ID == chunk ID.
    import uuid
    points = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        try:
            point_id = str(uuid.UUID(str(chunk["id"])))
        except (ValueError, KeyError, AttributeError):
            point_id = i  # fallback for non-UUID IDs
        points.append(models.PointStruct(id=point_id, vector=emb, payload=chunk))
    client.upsert(collection_name=COLLECTION, points=points)

def vector_search(client: QdrantClient, query_vector: list[float], top_k: int = 10):
    return client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
