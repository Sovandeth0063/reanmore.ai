"""
File: backend/ingestion/chunker.py
Description: Semantic and sliding-window chunker with Khmer language detection
             and deterministic chunk ID generation.
"""

from __future__ import annotations
import re
import hashlib
from typing import List, Optional, Dict, Any

try:
    from backend.ingestion.schemas import RawDocumentPage, DocumentChunk, GradeTier, SubjectArea
except ImportError:
    try:
        from ingestion.schemas import RawDocumentPage, DocumentChunk, GradeTier, SubjectArea
    except ImportError:
        from schemas import RawDocumentPage, DocumentChunk, GradeTier, SubjectArea


def detect_language(text: str) -> str:
    """
    Detects whether text is primarily Khmer, English, or Mixed.
    Khmer Unicode range is U+1780 to U+17FF.
    """
    if not text:
        return "en"

    khmer_chars = len(re.findall(r'[\u1780-\u17FF]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u1780-\u17FF]', text))

    if total_alpha == 0:
        return "en"

    ratio = khmer_chars / total_alpha
    if ratio > 0.40:
        return "km"
    elif ratio > 0.05:
        return "mixed"
    return "en"


def _generate_chunk_id(source_file: str, page_number: Optional[int], chunk_idx: int, text: str) -> str:
    """Creates a deterministic, reproducible hash-based chunk ID."""
    clean_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', source_file)
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]
    page_str = f"p{page_number}" if page_number is not None else "p0"
    return f"{clean_filename}_{page_str}_c{chunk_idx}_{text_hash}"


def chunk_document_page(
    page: RawDocumentPage,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
    default_grade: GradeTier = GradeTier.GRADE_4_6,
    default_subject: SubjectArea = SubjectArea.SCIENCE,
    default_chapter: Optional[str] = None,
) -> List[DocumentChunk]:
    """
    Chunks a single document page into overlapping text spans.
    Respects paragraph boundaries whenever possible to prevent cutting formulas or definitions.
    """
    text = page.text.strip()
    if not text:
        return []

    # If the whole page text is smaller than target chunk size + half overlap, keep as one chunk
    if len(text) <= (chunk_size + (chunk_overlap // 2)):
        chunk_id = _generate_chunk_id(page.source_file, page.page_number, 0, text)
        return [
            DocumentChunk(
                chunk_id=chunk_id,
                text=text,
                source_file=page.source_file,
                page_number=page.page_number,
                grade=default_grade,
                subject=default_subject,
                chapter=page.section_title or default_chapter,
                language=detect_language(text),
                metadata=page.metadata,
            )
        ]

    chunks: List[DocumentChunk] = []
    
    # Split by double newline (paragraphs) first
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk_parts: List[str] = []
    current_length = 0
    chunk_index = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        # If a single paragraph is longer than chunk_size, split by sliding window
        if len(para_clean) > chunk_size:
            # First flush any accumulated text
            if current_chunk_parts:
                combined = "\n\n".join(current_chunk_parts)
                chunk_id = _generate_chunk_id(page.source_file, page.page_number, chunk_index, combined)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=combined,
                        source_file=page.source_file,
                        page_number=page.page_number,
                        grade=default_grade,
                        subject=default_subject,
                        chapter=page.section_title or default_chapter,
                        language=detect_language(combined),
                        metadata=page.metadata,
                    )
                )
                chunk_index += 1
                current_chunk_parts = []
                current_length = 0

            # Window split long paragraph
            start = 0
            while start < len(para_clean):
                end = min(start + chunk_size, len(para_clean))
                # Try to break at a sentence or space boundary
                if end < len(para_clean):
                    last_space = para_clean.rfind(" ", start, end)
                    last_period = para_clean.rfind(". ", start, end)
                    break_point = max(last_period, last_space)
                    if break_point > start + (chunk_size // 2):
                        end = break_point + 1

                span = para_clean[start:end].strip()
                if span:
                    chunk_id = _generate_chunk_id(page.source_file, page.page_number, chunk_index, span)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            text=span,
                            source_file=page.source_file,
                            page_number=page.page_number,
                            grade=default_grade,
                            subject=default_subject,
                            chapter=page.section_title or default_chapter,
                            language=detect_language(span),
                            metadata=page.metadata,
                        )
                    )
                    chunk_index += 1

                if end >= len(para_clean):
                    break
                start = max(end - chunk_overlap, start + 1)
            continue

        # Accumulate paragraphs
        if current_length + len(para_clean) + 2 > chunk_size and current_chunk_parts:
            combined = "\n\n".join(current_chunk_parts)
            chunk_id = _generate_chunk_id(page.source_file, page.page_number, chunk_index, combined)
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    text=combined,
                    source_file=page.source_file,
                    page_number=page.page_number,
                    grade=default_grade,
                    subject=default_subject,
                    chapter=page.section_title or default_chapter,
                    language=detect_language(combined),
                    metadata=page.metadata,
                )
            )
            chunk_index += 1
            # Keep the last paragraph for overlap continuity if small enough
            if len(current_chunk_parts[-1]) <= chunk_overlap:
                current_chunk_parts = [current_chunk_parts[-1], para_clean]
                current_length = sum(len(p) for p in current_chunk_parts) + 2
            else:
                current_chunk_parts = [para_clean]
                current_length = len(para_clean)
        else:
            current_chunk_parts.append(para_clean)
            current_length += len(para_clean) + 2

    # Flush final accumulated chunk
    if current_chunk_parts:
        combined = "\n\n".join(current_chunk_parts)
        chunk_id = _generate_chunk_id(page.source_file, page.page_number, chunk_index, combined)
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                text=combined,
                source_file=page.source_file,
                page_number=page.page_number,
                grade=default_grade,
                subject=default_subject,
                chapter=page.section_title or default_chapter,
                language=detect_language(combined),
                metadata=page.metadata,
            )
        )

    return chunks
