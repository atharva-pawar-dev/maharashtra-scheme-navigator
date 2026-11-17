from __future__ import annotations

from typing import Callable

from qdrant_client import QdrantClient, models


class QdrantSemanticRetriever:
    """Optional Qdrant adapter; inject a local embedding function to keep inference offline."""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embed_query: Callable[[str], list[float]],
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embed_query = embed_query

    def search(self, query: str, limit: int = 10) -> list[tuple[str, float]]:
        vector = self.embed_query(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [(str(point.payload["doc_id"]), float(point.score)) for point in response.points if point.payload and point.payload.get("doc_id")]

    def ensure_collection(self, vector_size: int) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
