"""
File: orchestrator/app/services/rag/vector_store.py
Description: Qdrant vector store manager supporting embedded local persistence
             (backend/data/qdrant) or containerized Qdrant instance.
"""

from typing import List, Dict, Any, Optional
import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType
)

logger = logging.getLogger("reanmore.rag.vector_store")

COLLECTION_NAME = "reanmore_science_curriculum"
VECTOR_DIM = 384


class ScienceVectorStore:
    """
    Manages vector storage and similarity search for the Elementary Science curriculum.
    """

    def __init__(self, path: Optional[str] = None, url: Optional[str] = None):
        # Determine client mode: URL if specified or env var, otherwise local disk path
        qdrant_url = url or os.getenv("QDRANT_URL") or os.getenv("QDRANT_HOST")
        if qdrant_url:
            logger.info(f"Connecting to Qdrant server at: {qdrant_url}")
            self.client = QdrantClient(url=qdrant_url)
        else:
            local_path = path or os.getenv("QDRANT_PATH") or os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "data", "qdrant"
            )
            os.makedirs(local_path, exist_ok=True)
            logger.info(f"Using local embedded Qdrant storage at: {local_path}")
            self.client = QdrantClient(path=local_path)

        self.ensure_collection()

    def ensure_collection(self) -> None:
        """Create curriculum collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection '{COLLECTION_NAME}' (dim={VECTOR_DIM}, metric=COSINE)")

                # Create payload indexes for fast filtered searches
                for field, schema in [
                    ("grade_band", PayloadSchemaType.KEYWORD),
                    ("subject", PayloadSchemaType.KEYWORD),
                    ("unit", PayloadSchemaType.KEYWORD),
                    ("topic", PayloadSchemaType.KEYWORD),
                ]:
                    try:
                        self.client.create_payload_index(
                            collection_name=COLLECTION_NAME,
                            field_name=field,
                            field_schema=schema,
                        )
                    except Exception as idx_err:
                        logger.debug(f"Payload index creation note for {field}: {idx_err}")
        except Exception as e:
            logger.error(f"Error ensuring collection '{COLLECTION_NAME}': {e}")

    def upsert_documents(self, documents: List[Dict[str, Any]], vectors: List[List[float]]) -> int:
        """
        Upsert a batch of document payloads and vectors.
        Each doc must have 'id' (int or str), 'text', 'title', etc.
        """
        if len(documents) != len(vectors):
            raise ValueError("Number of documents must match number of vectors.")

        points = []
        for i, (doc, vec) in enumerate(zip(documents, vectors)):
            point_id = doc.get("doc_id", i + 1)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "id": doc.get("id", f"doc_{i}"),
                        "title": doc.get("title", ""),
                        "text": doc.get("text", ""),
                        "subject": doc.get("subject", "science"),
                        "unit": doc.get("unit", ""),
                        "topic": doc.get("topic", ""),
                        "grade_band": doc.get("grade_band", "grade_1_3"),
                        "source": doc.get("source", ""),
                        "key_concepts": doc.get("key_concepts", []),
                    }
                )
            )

        self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"Upserted {len(points)} documents into '{COLLECTION_NAME}'")
        return len(points)

    def search(
        self,
        query_vector: List[float],
        grade_band: Optional[str] = None,
        top_k: int = 3,
        min_score: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Execute filtered cosine similarity search.
        """
        query_filter = None
        if grade_band:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="grade_band",
                        match=MatchValue(value=grade_band)
                    )
                ]
            )

        # Execute search with fallback if strict grade filter yields nothing
        resp = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=min_score,
        )
        hits = resp.points if hasattr(resp, "points") else resp

        # If strict grade filter had 0 results, fall back to global search
        if not hits and query_filter:
            resp = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
                score_threshold=min_score,
            )
            hits = resp.points if hasattr(resp, "points") else resp

        output = []
        for hit in hits:
            item = dict(hit.payload or {})
            item["score"] = float(hit.score)
            output.append(item)

        return output


_vector_store_instance: Optional[ScienceVectorStore] = None


def get_vector_store() -> ScienceVectorStore:
    """Singleton getter for the science vector store."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ScienceVectorStore()
    return _vector_store_instance
