from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

from app.rag.embedder import Embedder

_COLLECTION = "menu_items"


class MenuRetriever:
    """
    Read path of the RAG pipeline.

    Takes a natural-language query, embeds it, and returns the most
    semantically similar menu items — optionally filtered by structured
    attributes (is_veg, cuisine, max_calories, min_protein).

    This is the core of RAG: retrieval BEFORE generation.
    The Recommendation Agent (Phase 7) calls this to get candidate dishes,
    then passes them to the LLM to generate a natural-language recommendation.
    """

    def __init__(self, client: AsyncQdrantClient, embedder: Embedder) -> None:
        self.client = client
        self.embedder = embedder

    async def search(
        self,
        query: str,
        limit: int = 10,
        is_veg: bool | None = None,
        cuisine: str | None = None,
        max_calories: int | None = None,
        min_protein: float | None = None,
    ) -> list[dict]:
        """
        Semantic search with optional pre-filtering.

        Filtering happens BEFORE vector similarity — Qdrant scans only
        the points that match the filter, then ranks by cosine similarity.
        This is more efficient and accurate than post-filtering.
        """
        vector = await self.embedder.embed(query)

        must_conditions: list = [
            FieldCondition(key="is_available", match=MatchValue(value=True))
        ]

        if is_veg is not None:
            must_conditions.append(
                FieldCondition(key="is_veg", match=MatchValue(value=is_veg))
            )
        if cuisine:
            must_conditions.append(
                FieldCondition(key="cuisine", match=MatchValue(value=cuisine))
            )
        if max_calories is not None:
            must_conditions.append(
                FieldCondition(key="calories", range=Range(lte=max_calories))
            )
        if min_protein is not None:
            must_conditions.append(
                FieldCondition(key="protein_g", range=Range(gte=min_protein))
            )

        # qdrant-client 1.7+ replaced search() with query_points()
        response = await self.client.query_points(
            collection_name=_COLLECTION,
            query=vector,
            limit=limit,
            query_filter=Filter(must=must_conditions),
            with_payload=True,
        )

        return [{"score": round(r.score, 4), **r.payload} for r in response.points]
