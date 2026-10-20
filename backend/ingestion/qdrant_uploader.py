"""
File: backend/ingestion/qdrant_uploader.py
Description: Qdrant vector database collection creator, payload indexer, and batch upsert engine.
"""

from __future__ import annotations
import uuid
import logging
from typing import List, Dict, Any, Optional

try:
    from backend.ingestion.schemas import DocumentChunk
except ImportError:
    try:
        from ingestion.schemas import DocumentChunk
    except ImportError:
        from schemas import DocumentChunk

logger = logging.getLogger("ingestion.qdrant")


class QdrantUploader:
    """
    Manages Qdrant collections, index definitions, and batch point upserts.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "science_curriculum_v2",
        vector_dim: int = 768,
        dry_run: bool = False
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.dry_run = dry_run
        self._client = None

    def _get_client(self):
        if self._client is None and not self.dry_run:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(host=self.host, port=self.port, timeout=10.0)
            except Exception as e:
                logger.error(f"Could not connect to Qdrant at {self.host}:{self.port}: {e}")
                raise ConnectionError(
                    f"Failed to connect to Qdrant at http://{self.host}:{self.port}. Is the docker container running?"
                )
        return self._client

    def ensure_collection(self):
        """
        Creates the Qdrant collection if it does not already exist,
        and creates payload indexes on critical filtering fields.
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create/verify collection '{self.collection_name}' (768-dim, Cosine)")
            return

        from qdrant_client.http import models

        client = self._get_client()
        existing = [c.name for c in client.get_collections().collections]

        if self.collection_name not in existing:
            logger.info(f"Creating collection '{self.collection_name}' with {self.vector_dim} dimensions...")
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_dim,
                    distance=models.Distance.COSINE
                )
            )

            # Create payload indexes for fast metadata filtering (required by Socratic RAG)
            indexed_fields = ["grade", "subject", "chapter", "source_file", "language"]
            for field in indexed_fields:
                try:
                    client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    logger.info(f"Created payload index on '{field}' in '{self.collection_name}'")
                except Exception as e:
                    logger.warning(f"Could not create payload index on '{field}': {e}")
        else:
            logger.info(f"Collection '{self.collection_name}' already exists.")

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        vectors: List[List[float]],
        batch_size: int = 50
    ) -> int:
        """
        Uploads chunks and vectors to Qdrant in batches.
        """
        if len(chunks) != len(vectors):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(vectors)} vectors")

        if not chunks:
            return 0

        if self.dry_run:
            logger.info(f"[DRY RUN] Would upsert {len(chunks)} points to '{self.collection_name}'")
            return len(chunks)

        from qdrant_client.http import models

        client = self._get_client()
        total_upserted = 0

        for i in range(0, len(chunks), batch_size):
            chunk_slice = chunks[i : i + batch_size]
            vector_slice = vectors[i : i + batch_size]

            points = []
            for chunk, vec in zip(chunk_slice, vector_slice):
                # Generate a reproducible UUIDv5 from chunk_id for Qdrant compatibility
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "source_file": chunk.source_file,
                    "page_number": chunk.page_number,
                    "grade": chunk.grade.value if hasattr(chunk.grade, "value") else str(chunk.grade),
                    "subject": chunk.subject.value if hasattr(chunk.subject, "value") else str(chunk.subject),
                    "chapter": chunk.chapter,
                    "subtopic": chunk.subtopic,
                    "language": chunk.language,
                    "created_at": chunk.created_at,
                    "metadata": chunk.metadata,
                }
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vec,
                        payload=payload
                    )
                )

            client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            total_upserted += len(points)
            logger.info(f"Upserted {total_upserted}/{len(chunks)} chunks to '{self.collection_name}'")

        return total_upserted
