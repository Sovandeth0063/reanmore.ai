"""
File: backend/ingestion/schemas.py
Description: Pydantic schemas and data contracts for Curriculum & Document Ingestion Pipeline.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import datetime


class GradeTier(str, Enum):
    GRADE_1_3 = "grade_1_3"
    GRADE_4_6 = "grade_4_6"
    GRADE_7_9 = "grade_7_9"
    GENERAL = "general"


class SubjectArea(str, Enum):
    SCIENCE = "science"
    MATH = "math"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    GENERAL = "general"


class RawDocumentPage(BaseModel):
    """Represents a raw extracted page or section from an input document."""
    source_file: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """Standardized metadata-rich chunk prepared for vector embedding and storage."""
    chunk_id: str = Field(..., description="Unique deterministic identifier for the chunk")
    text: str = Field(..., description="Cleaned, normalized text content")
    source_file: str = Field(..., description="Filename or document URI")
    page_number: Optional[int] = Field(default=None, description="Physical page number in source book")
    grade: GradeTier = Field(default=GradeTier.GRADE_4_6, description="Educational grade level")
    subject: SubjectArea = Field(default=SubjectArea.SCIENCE, description="Academic subject domain")
    chapter: Optional[str] = Field(default=None, description="Chapter or unit title")
    subtopic: Optional[str] = Field(default=None, description="Specific scientific/math concept")
    language: str = Field(default="km", description="Detected language: km, en, or mixed")
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionConfig(BaseModel):
    """Configuration options for an ingestion batch run."""
    collection_name: str = Field(default="science_curriculum_v2", description="Target Qdrant collection")
    chunk_size: int = Field(default=600, ge=100, le=4000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="Overlap between consecutive chunks")
    embedding_model: str = Field(default="models/text-embedding-004", description="Gemini embedding model")
    embedding_dim: int = Field(default=768, description="Vector dimension size")
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant HTTP port")
    batch_size: int = Field(default=25, ge=1, le=100, description="Embedding and upsert batch size")
    dry_run: bool = Field(default=False, description="If True, parse and chunk without embedding or upserting")


class IngestionReport(BaseModel):
    """Execution summary emitted after an ingestion run."""
    total_files_processed: int = 0
    total_pages_extracted: int = 0
    total_chunks_created: int = 0
    total_points_upserted: int = 0
    collection_name: str
    duration_seconds: float = 0.0
    errors: List[str] = Field(default_factory=list)
