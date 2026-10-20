"""
File: backend/ingestion/ingest_science_curriculum.py
Description: Ingests the 6 Core Elementary Science Curriculum Units into Qdrant
             using the local offline FastEmbed embedder.
"""

import os
import sys
import json
import logging

# Ensure orchestrator is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
if ORCHESTRATOR_DIR not in sys.path:
    sys.path.insert(0, ORCHESTRATOR_DIR)

from app.services.rag.embedder import get_embedder
from app.services.rag.vector_store import get_vector_store, COLLECTION_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_science")


def run_ingestion(data_file: str = None) -> int:
    if data_file is None:
        data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data_sources",
            "science_curriculum_en.json"
        )

    logger.info(f"Loading science curriculum data from: {data_file}")
    with open(data_file, "r", encoding="utf-8") as f:
        passages = json.load(f)

    logger.info(f"Loaded {len(passages)} science textbook chapters/passages.")

    embedder = get_embedder()
    vector_store = get_vector_store()

    texts_to_embed = [
        f"{p.get('title', '')}: {p.get('text', '')} Keywords: {', '.join(p.get('key_concepts', []))}"
        for p in passages
    ]

    logger.info("Generating local 384-dim FastEmbed embeddings...")
    vectors = embedder.embed_documents(texts_to_embed)
    logger.info(f"Generated {len(vectors)} embeddings.")

    # Assign integer doc_ids for Qdrant
    for i, p in enumerate(passages):
        p["doc_id"] = i + 1

    logger.info(f"Upserting into Qdrant collection '{COLLECTION_NAME}'...")
    count = vector_store.upsert_documents(documents=passages, vectors=vectors)
    logger.info(f"Successfully indexed {count} science passages into Qdrant!")
    return count


if __name__ == "__main__":
    count = run_ingestion()
    print(f"\n[DONE] Successfully ingested {count} science passages into Qdrant!")
