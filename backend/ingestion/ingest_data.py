"""
File: backend/ingestion/ingest_data.py
Description: Data Ingestion Pipeline runner. Upgraded to support both legacy science_reference.json
             and arbitrary curriculum files (PDF, Markdown, JSON) with payload metadata indexing.
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    for env_path in [Path(".env"), Path("backend/.env"), Path("../../.env")]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

try:
    from backend.ingestion.pipeline import CurriculumIngestionPipeline, IngestionConfig
    from backend.ingestion.schemas import GradeTier, SubjectArea
except ImportError:
    from pipeline import CurriculumIngestionPipeline, IngestionConfig
    from schemas import GradeTier, SubjectArea


def main():
    # If arguments are passed, pass through to pipeline CLI
    if len(sys.argv) > 1:
        from pipeline import main as cli_main
        cli_main()
        return

    # Default legacy run: ingest science_reference.json
    data_file = Path(__file__).parent / "data_sources" / "science_reference.json"
    if not data_file.exists():
        print(f"[ERROR] Data file not found at: {data_file}")
        return

    print("Running default ingestion for science_reference.json...")
    config = IngestionConfig(
        collection_name=os.getenv("QDRANT_COLLECTION", "science_curriculum_v2"),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", 6333)),
        dry_run=not bool(os.getenv("GEMINI_API_KEY")),
    )

    pipeline = CurriculumIngestionPipeline(config=config)
    report = pipeline.run_file(
        file_path=data_file,
        grade=GradeTier.GRADE_4_6,
        subject=SubjectArea.SCIENCE,
        chapter="General Science Reference"
    )

    print("\n" + "=" * 50)
    print("      DATA INGESTION PIPELINE COMPLETE")
    print("=" * 50)
    print(f"Chunks Created  : {report.total_chunks_created}")
    print(f"Points Upserted : {report.total_points_upserted}")
    print(f"Duration        : {report.duration_seconds:.2f}s")
    if report.errors:
        print(f"Errors          : {report.errors}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
