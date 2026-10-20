"""
File: backend/ingestion/verify_retrieval.py
Description: Fast CLI tool to test and verify vector retrieval against Qdrant collections.
Usage:
  python -m backend.ingestion.verify_retrieval --query "How do plants drink water?" --grade grade_4_6 --subject science
"""

from __future__ import annotations
import os
import sys
import argparse
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    for env_path in [Path(".env"), Path("backend/.env"), Path("../../.env")]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    print("[ERROR] qdrant-client not installed. Install via: pip install qdrant-client")
    sys.exit(1)


def test_retrieval(
    query: str,
    collection_name: str = "science_curriculum_v2",
    grade: Optional[str] = None,
    subject: Optional[str] = None,
    top_k: int = 3,
    host: str = "localhost",
    port: int = 6333,
    api_key: Optional[str] = None,
):
    print("\n" + "=" * 65)
    print("        REANMORE VECTOR RETRIEVAL VERIFICATION TOOL")
    print("=" * 65)
    print(f"Query       : \"{query}\"")
    print(f"Collection  : {collection_name}")
    print(f"Filter Grade: {grade or 'None (All)'}")
    print(f"Filter Subj : {subject or 'None (All)'}")
    print("=" * 65 + "\n")

    # 1. Connect to Qdrant
    try:
        client = QdrantClient(host=host, port=port, timeout=5.0)
        collections = [c.name for c in client.get_collections().collections]
        if collection_name not in collections:
            print(f"[ERROR] Collection '{collection_name}' does not exist in Qdrant!")
            print(f"Available collections: {collections}")
            return
    except Exception as e:
        print(f"[ERROR] Could not connect to Qdrant at {host}:{port}: {e}")
        return

    # 2. Embed Query
    gemini_key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print("[ERROR] GEMINI_API_KEY not set. Cannot embed query text.")
        return

    try:
        from google import genai
        ai_client = genai.Client(api_key=gemini_key)
        emb_resp = ai_client.models.embed_content(
            model="models/text-embedding-004",
            contents=query,
        )
        query_vector = list(emb_resp.embeddings[0].values)
    except Exception as e:
        print(f"[ERROR] Failed to generate query embedding: {e}")
        return

    # 3. Build Metadata Filters
    must_filters = []
    if grade:
        must_filters.append(models.FieldCondition(key="grade", match=models.MatchValue(value=grade)))
    if subject:
        must_filters.append(models.FieldCondition(key="subject", match=models.MatchValue(value=subject)))

    query_filter = models.Filter(must=must_filters) if must_filters else None

    # 4. Search Qdrant
    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
    except Exception as e:
        print(f"[ERROR] Qdrant search failed: {e}")
        return

    if not results:
        print("⚠️ No matching chunks found.")
        return

    print(f"Found {len(results)} relevant curriculum chunks:\n")
    for idx, hit in enumerate(results):
        score = hit.score
        payload = hit.payload or {}
        text = payload.get("text", "")
        source = payload.get("source_file", "unknown")
        page = payload.get("page_number", "N/A")
        sub = payload.get("subject", "N/A")
        grd = payload.get("grade", "N/A")

        print(f"--- [Match {idx + 1}] Similarity Score: {score:.4f} ---")
        print(f"Source : {source} (Page {page}) | Grade: {grd} | Subject: {sub}")
        print(f"Content:\n{text[:300]}..." if len(text) > 300 else f"Content:\n{text}")
        print("-" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Test and verify curriculum retrieval in Qdrant")
    parser.add_argument("--query", "-q", type=str, required=True, help="Test query string")
    parser.add_argument("--collection", "-c", type=str, default="science_curriculum_v2")
    parser.add_argument("--grade", "-g", type=str, default=None)
    parser.add_argument("--subject", "-s", type=str, default=None)
    parser.add_argument("--top-k", "-k", type=int, default=3)
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=6333)
    parser.add_argument("--api-key", type=str, default=None)

    args = parser.parse_args()

    test_retrieval(
        query=args.query,
        collection_name=args.collection,
        grade=args.grade,
        subject=args.subject,
        top_k=args.top_k,
        host=args.host,
        port=args.port,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
