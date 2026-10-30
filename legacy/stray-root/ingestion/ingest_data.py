"""
File: ingestion/ingest_data.py
Description: Data Ingestion Pipeline. Reads science reference data from science_reference.json,
             generates vector embeddings using Gemini, and uploads them to Qdrant collections.
"""

import os
import json
import uuid
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY environment variable is not set.")
    print("Please set it in your environment before running this script.")
    import sys
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# 2. Initialize Qdrant Client
# Connects to localhost (host machine) by default, or QDRANT_HOST if running inside docker
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

print(f"Connecting to Qdrant at http://{QDRANT_HOST}:{QDRANT_PORT}...")
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
except Exception as e:
    print(f"[ERROR] Failed to connect to Qdrant: {e}")
    import sys
    sys.exit(1)

# 3. Embedding Helper
def get_embedding(text: str) -> list:
    """
    Generates a 768-dimension vector embedding for the input text using Gemini.
    """
    try:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Warning: failed to get embedding with models/text-embedding-004: {e}. Trying models/embedding-001...")
        # Fallback to older embedding model (768 dimensions as well)
        response = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]

def main():
    # 4. Load Science Reference Data
    data_file = os.path.join(os.path.dirname(__file__), "data_sources", "science_reference.json")
    if not os.path.exists(data_file):
        print(f"[ERROR] Data file not found at: {data_file}")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    # Track created collections to avoid redundant requests
    created_collections = set()

    print(f"Loaded {len(documents)} document entries for ingestion.")

    for idx, doc in enumerate(documents):
        collection_name = doc.get("collection")
        keyword = doc.get("keyword")
        text = doc.get("text")
        steps = doc.get("steps", [])

        if not collection_name or not text or not keyword:
            print(f"Skipping entry {idx+1}: missing collection, keyword, or text.")
            continue

        print(f"\nProcessing [{collection_name}] -> '{keyword}'...")

        # 5. Create Collection if not already done
        if collection_name not in created_collections:
            # Check if collection exists in Qdrant
            collections_list = qdrant_client.get_collections().collections
            exists = any(c.name == collection_name for c in collections_list)
            
            if not exists:
                print(f"Creating collection '{collection_name}' with 768 dimensions...")
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=768,  # Gemini text-embedding-004 uses 768 dimensions
                        distance=models.Distance.COSINE
                    )
                )
            created_collections.add(collection_name)

        # 6. Generate Vector Embedding
        print("Generating embedding vector...")
        vector = get_embedding(text)

        # 7. Upload Point to Qdrant
        point_id = str(uuid.uuid4())
        payload = {
            "keyword": keyword,
            "text": text,
            "steps": steps
        }

        print(f"Uploading point {point_id} to Qdrant...")
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print(f"Ingested successfully!")

    print("\n==============================================")
    print("      DATA INGESTION PIPELINE COMPLETE        ")
    print("==============================================")

if __name__ == "__main__":
    main()
