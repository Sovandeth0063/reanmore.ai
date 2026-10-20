"""
File: backend/ingestion/pipeline.py
Description: Master CLI and programmatic entrypoint for the Curriculum Ingestion Pipeline.
Usage:
  python -m backend.ingestion.pipeline --file path/to/document.pdf --grade grade_4_6 --subject science
  python -m backend.ingestion.pipeline --dir path/to/textbooks/ --grade grade_1_3 --subject math
  python -m backend.ingestion.pipeline --file backend/ingestion/data_sources/science_reference.json --dry-run
"""

from __future__ import annotations
import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Automatically locate and load .env files
try:
    from dotenv import load_dotenv
    # Check current dir, backend dir, and root dir
    for env_path in [Path(".env"), Path("backend/.env"), Path("../../.env")]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

try:
    from backend.ingestion.schemas import (
        GradeTier, SubjectArea, DocumentChunk, IngestionConfig, IngestionReport
    )
    from backend.ingestion.parser import parse_document
    from backend.ingestion.chunker import chunk_document_page
    from backend.ingestion.embedder import EmbeddingEngine
    from backend.ingestion.qdrant_uploader import QdrantUploader
except ImportError:
    from schemas import (
        GradeTier, SubjectArea, DocumentChunk, IngestionConfig, IngestionReport
    )
    from parser import parse_document
    from chunker import chunk_document_page
    from embedder import EmbeddingEngine
    from qdrant_uploader import QdrantUploader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ingestion.pipeline")


class CurriculumIngestionPipeline:
    """
    End-to-end ingestion orchestrator:
    1. Parse raw files (PDF, Markdown, JSON, CSV)
    2. Normalize & segment into semantic chunks
    3. Detect language & attach curriculum metadata
    4. Generate 768-dim embeddings via Google GenAI
    5. Upsert to Qdrant with payload indexing
    """

    def __init__(self, config: Optional[IngestionConfig] = None, api_key: Optional[str] = None):
        self.config = config or IngestionConfig()
        self.embedder = EmbeddingEngine(
            api_key=api_key,
            model_name=self.config.embedding_model,
            expected_dim=self.config.embedding_dim,
            dry_run=self.config.dry_run,
        )
        self.uploader = QdrantUploader(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port,
            collection_name=self.config.collection_name,
            vector_dim=self.config.embedding_dim,
            dry_run=self.config.dry_run,
        )

    def process_file(
        self,
        file_path: Path,
        grade: GradeTier = GradeTier.GRADE_4_6,
        subject: SubjectArea = SubjectArea.SCIENCE,
        chapter: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """Parses and chunks a single file without uploading."""
        logger.info(f"Parsing document: {file_path.name}")
        pages = parse_document(file_path)
        logger.info(f"Extracted {len(pages)} logical pages/sections from {file_path.name}")

        all_chunks: List[DocumentChunk] = []
        for page in pages:
            chunks = chunk_document_page(
                page=page,
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                default_grade=grade,
                default_subject=subject,
                default_chapter=chapter,
            )
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks for {file_path.name}")
        return all_chunks

    def run_file(
        self,
        file_path: Path,
        grade: GradeTier = GradeTier.GRADE_4_6,
        subject: SubjectArea = SubjectArea.SCIENCE,
        chapter: Optional[str] = None,
    ) -> IngestionReport:
        """Processes a single file and upserts it to Qdrant."""
        start_time = time.time()
        report = IngestionReport(collection_name=self.config.collection_name)

        try:
            chunks = self.process_file(file_path, grade, subject, chapter)
            report.total_files_processed = 1
            report.total_chunks_created = len(chunks)

            if not chunks:
                logger.warning(f"No text chunks extracted from {file_path}")
                report.duration_seconds = time.time() - start_time
                return report

            # Ensure Qdrant collection and payload indexes exist
            self.uploader.ensure_collection()

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            texts = [c.text for c in chunks]
            vectors = self.embedder.embed_texts(texts)

            # Upsert into Qdrant
            logger.info(f"Upserting {len(chunks)} points into Qdrant collection '{self.config.collection_name}'...")
            upserted = self.uploader.upsert_chunks(
                chunks=chunks,
                vectors=vectors,
                batch_size=self.config.batch_size
            )
            report.total_points_upserted = upserted

        except Exception as e:
            logger.error(f"Ingestion failed for {file_path}: {e}")
            report.errors.append(str(e))

        report.duration_seconds = time.time() - start_time
        return report

    def run_directory(
        self,
        dir_path: Path,
        grade: GradeTier = GradeTier.GRADE_4_6,
        subject: SubjectArea = SubjectArea.SCIENCE,
        chapter: Optional[str] = None,
        extensions: Optional[List[str]] = None,
    ) -> IngestionReport:
        """Processes all supported documents in a directory."""
        start_time = time.time()
        valid_exts = set(extensions or [".pdf", ".md", ".txt", ".json", ".csv"])
        report = IngestionReport(collection_name=self.config.collection_name)

        files = [p for p in dir_path.glob("**/*") if p.is_file() and p.suffix.lower() in valid_exts]
        logger.info(f"Found {len(files)} supported files in {dir_path}")

        all_chunks: List[DocumentChunk] = []
        for f in files:
            try:
                chunks = self.process_file(f, grade, subject, chapter)
                all_chunks.extend(chunks)
                report.total_files_processed += 1
            except Exception as e:
                logger.error(f"Failed parsing file {f.name}: {e}")
                report.errors.append(f"{f.name}: {e}")

        report.total_chunks_created = len(all_chunks)
        if not all_chunks:
            logger.warning("No chunks created from directory.")
            report.duration_seconds = time.time() - start_time
            return report

        try:
            self.uploader.ensure_collection()
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            texts = [c.text for c in all_chunks]
            vectors = self.embedder.embed_texts(texts)

            upserted = self.uploader.upsert_chunks(
                chunks=all_chunks,
                vectors=vectors,
                batch_size=self.config.batch_size
            )
            report.total_points_upserted = upserted
        except Exception as e:
            logger.error(f"Batch upload failed: {e}")
            report.errors.append(str(e))

        report.duration_seconds = time.time() - start_time
        return report


def main():
    parser = argparse.ArgumentParser(
        description="ReanMore Curriculum & Document Ingestion Pipeline"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", type=str, help="Path to a single document (PDF, MD, TXT, JSON, CSV)")
    group.add_argument("--dir", "-d", type=str, help="Path to a directory containing curriculum files")

    parser.add_argument("--grade", "-g", type=str, default="grade_4_6",
                        choices=["grade_1_3", "grade_4_6", "grade_7_9", "general"],
                        help="Target student grade level tier (default: grade_4_6)")
    parser.add_argument("--subject", "-s", type=str, default="science",
                        choices=["science", "math", "physics", "chemistry", "biology", "general"],
                        help="Curriculum subject domain (default: science)")
    parser.add_argument("--chapter", type=str, default=None,
                        help="Optional chapter or unit name override")
    parser.add_argument("--collection", "-c", type=str, default="science_curriculum_v2",
                        help="Qdrant collection name (default: science_curriculum_v2)")
    parser.add_argument("--chunk-size", type=int, default=600,
                        help="Target character length per chunk (default: 600)")
    parser.add_argument("--chunk-overlap", type=int, default=100,
                        help="Overlap characters between chunks (default: 100)")
    parser.add_argument("--qdrant-host", type=str, default="localhost",
                        help="Qdrant host (default: localhost)")
    parser.add_argument("--qdrant-port", type=int, default=6333,
                        help="Qdrant HTTP port (default: 6333)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Google Gemini API key (defaults to GEMINI_API_KEY env)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run parser and chunker without calling embedding API or Qdrant")

    args = parser.parse_args()

    config = IngestionConfig(
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        dry_run=args.dry_run,
    )

    grade = GradeTier(args.grade)
    subject = SubjectArea(args.subject)

    pipeline = CurriculumIngestionPipeline(config=config, api_key=args.api_key)

    print("\n" + "=" * 60)
    print("      REANMORE CURRICULUM INGESTION PIPELINE")
    print("=" * 60)
    print(f"Target Collection : {config.collection_name}")
    print(f"Target Grade      : {grade.value}")
    print(f"Target Subject    : {subject.value}")
    print(f"Dry Run Mode      : {config.dry_run}")
    print("=" * 60 + "\n")

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            sys.exit(1)
        report = pipeline.run_file(file_path, grade=grade, subject=subject, chapter=args.chapter)
    else:
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"[ERROR] Directory not found: {dir_path}")
            sys.exit(1)
        report = pipeline.run_directory(dir_path, grade=grade, subject=subject, chapter=args.chapter)

    print("\n" + "=" * 60)
    print("                 INGESTION REPORT")
    print("=" * 60)
    print(f"Files Processed   : {report.total_files_processed}")
    print(f"Chunks Created    : {report.total_chunks_created}")
    print(f"Points Upserted   : {report.total_points_upserted}")
    print(f"Duration          : {report.duration_seconds:.2f} seconds")
    if report.errors:
        print(f"Errors ({len(report.errors)}) :")
        for err in report.errors:
            print(f"  - {err}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
