"""
File: backend/ingestion/parser.py
Description: Multi-format document parser extracting clean text, pages, and section headers.
             Supports PDF (PyMuPDF), Markdown, Plain Text, JSON, and CSV.
"""

from __future__ import annotations
import os
import json
import csv
import re
from pathlib import Path
from typing import List, Optional
import logging

# Local fallback for standalone script execution
try:
    from backend.ingestion.schemas import RawDocumentPage
except ImportError:
    try:
        from ingestion.schemas import RawDocumentPage
    except ImportError:
        from schemas import RawDocumentPage

logger = logging.getLogger("ingestion.parser")


def _clean_text_noise(text: str) -> str:
    """Removes typical OCR and PDF artifacts like broken line wraps and null bytes."""
    if not text:
        return ""
    # Strip null characters and control characters
    text = text.replace("\x00", "").replace("\r\n", "\n")
    # Clean zero-width space
    text = text.replace("\u200b", "")
    # Unbreak hyphenated words at line ends (e.g., "pho-\ntosynthesis" -> "photosynthesis")
    text = re.sub(r'(\b[A-Za-z]+)-\n([A-Za-z]+\b)', r'\1\2', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_pdf(file_path: Path) -> List[RawDocumentPage]:
    """Extracts text page-by-page from a PDF using PyMuPDF."""
    pages: List[RawDocumentPage] = []
    try:
        import pymupdf  # PyMuPDF
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            raise ImportError(
                "PyMuPDF is required to parse PDF documents. Install via: pip install pymupdf"
            )

    doc = pymupdf.open(str(file_path))
    filename = file_path.name

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        raw_text = page.get_text("text") or ""
        cleaned = _clean_text_noise(raw_text)

        if not cleaned:
            continue

        pages.append(
            RawDocumentPage(
                source_file=filename,
                page_number=page_idx + 1,
                text=cleaned,
                metadata={
                    "total_pages": len(doc),
                    "file_type": "pdf"
                }
            )
        )
    doc.close()
    return pages


def parse_markdown_or_text(file_path: Path) -> List[RawDocumentPage]:
    """
    Parses Markdown or Text files.
    Splits along major headings (H1/H2) to preserve logical topic boundaries.
    """
    pages: List[RawDocumentPage] = []
    filename = file_path.name
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    cleaned = _clean_text_noise(content)
    if not cleaned:
        return []

    # Split by Markdown H1/H2 headings if present
    sections = re.split(r'\n(?=#{1,2}\s+)', cleaned)
    if len(sections) > 1:
        for idx, sec in enumerate(sections):
            sec_text = sec.strip()
            if not sec_text:
                continue
            # Extract section title from heading
            first_line = sec_text.split("\n", 1)[0]
            title = re.sub(r'^#{1,3}\s*', '', first_line).strip()
            pages.append(
                RawDocumentPage(
                    source_file=filename,
                    page_number=idx + 1,
                    section_title=title,
                    text=sec_text,
                    metadata={"file_type": "markdown"}
                )
            )
    else:
        pages.append(
            RawDocumentPage(
                source_file=filename,
                page_number=1,
                text=cleaned,
                metadata={"file_type": "text"}
            )
        )
    return pages


def parse_json(file_path: Path) -> List[RawDocumentPage]:
    """
    Parses JSON files. Supports:
    1. List of dicts (e.g. [{"keyword": "...", "text": "...", "steps": [...]}])
    2. Dict with "documents" or "data" list
    """
    pages: List[RawDocumentPage] = []
    filename = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("documents") or data.get("items") or data.get("data") or [data]

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        text_content = item.get("text") or item.get("content") or item.get("description") or ""
        keyword = item.get("keyword") or item.get("title") or item.get("topic") or ""
        steps = item.get("steps") or []

        # If steps exist, format into rich text representation
        if steps and isinstance(steps, list):
            steps_str = "\n".join([f"- Step {i+1}: {s}" for i, s in enumerate(steps)])
            full_text = f"{keyword}\n{text_content}\n\nMilestone Steps:\n{steps_str}".strip()
        else:
            full_text = f"{keyword}\n{text_content}".strip() if keyword else text_content

        cleaned = _clean_text_noise(full_text)
        if not cleaned:
            continue

        pages.append(
            RawDocumentPage(
                source_file=filename,
                page_number=idx + 1,
                section_title=keyword or None,
                text=cleaned,
                metadata={
                    "file_type": "json",
                    "original_item": {k: v for k, v in item.items() if k not in ["text", "content"]}
                }
            )
        )
    return pages


def parse_csv(file_path: Path) -> List[RawDocumentPage]:
    """Parses CSV files where rows represent concepts, Q&As, or vocabulary."""
    pages: List[RawDocumentPage] = []
    filename = file_path.name

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Combine non-empty fields into a coherent readable chunk
            parts = [f"{col}: {val}" for col, val in row.items() if val and val.strip()]
            if not parts:
                continue
            text = "\n".join(parts)
            pages.append(
                RawDocumentPage(
                    source_file=filename,
                    page_number=idx + 1,
                    text=_clean_text_noise(text),
                    metadata={"file_type": "csv"}
                )
            )
    return pages


def parse_document(file_path: Union[str, Path]) -> List[RawDocumentPage]:
    """
    Main dispatch parser. Automatically selects the correct extraction routine
    based on the file extension.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    elif ext in [".md", ".markdown", ".txt"]:
        return parse_markdown_or_text(path)
    elif ext == ".json":
        return parse_json(path)
    elif ext == ".csv":
        return parse_csv(path)
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: .pdf, .md, .txt, .json, .csv"
        )
