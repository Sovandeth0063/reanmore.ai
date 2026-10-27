"""Utility script to test a full PDF worksheet against the Homework Scanner pipeline
and save the structured JSON pages into `services/homework_scanner/sample_outputs/`.

Usage:
    python services/homework_scanner/scripts/run_worksheet_test.py --pdf path/to/worksheet.pdf
"""

import os
import sys
import json
import time
import argparse

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Set paths
script_dir = os.path.dirname(os.path.abspath(__file__))
hw_scanner_dir = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, hw_scanner_dir)

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv(os.path.join(hw_scanner_dir, ".env"), override=True)

# pyrefly: ignore [missing-import]
from app.services.ocr.pipeline.processor import HomeworkProcessor


def main():
    parser = argparse.ArgumentParser(description="Test PDF worksheet with Homework Scanner.")
    parser.add_argument(
        "--pdf", "-p",
        default=r"E:\Competition\Khmer Enterprise\Maths and Science Practice Worksheet.pdf",
        help="Path to PDF worksheet file"
    )
    args = parser.parse_args()

    pdf_path = os.path.abspath(args.pdf)
    if not os.path.exists(pdf_path):
        # Also check in sample_inputs
        rel_path = os.path.join(hw_scanner_dir, "sample_inputs", args.pdf)
        if os.path.exists(rel_path):
            pdf_path = rel_path
        else:
            print(f"Error: File {args.pdf} not found!")
            sys.exit(1)

    print("=" * 60)
    print(f"📖 Testing Worksheet: {pdf_path}")
    print("=" * 60)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    print(f"File Size: {len(pdf_bytes) / 1024:.1f} KB")

    # Initialize processor
    print("Initializing HomeworkProcessor...")
    processor = HomeworkProcessor()
    print(f"Active VLM Provider: {type(processor._vlm).__name__}")

    output_dir = os.path.join(hw_scanner_dir, "sample_outputs")
    os.makedirs(output_dir, exist_ok=True)

    # Process PDF
    t_start = time.perf_counter()
    print("\nRunning extraction pipeline on all pages...")
    response = processor.process(file_bytes=pdf_bytes, filename=os.path.basename(pdf_path))
    total_time = time.perf_counter() - t_start

    print(f"\n✅ Processing Finished in {total_time:.2f}s!")
    print(f"Total Pages Processed: {len(response.pages)}")
    print(f"Overall Document Confidence: {response.confidence}")
    print(f"Stage Timers: {response.stage_timers}")

    for i, page in enumerate(response.pages, 1):
        page_dict = page.model_dump(exclude_none=True)
        out_file = os.path.join(output_dir, f"page_{i}_result.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(page_dict, f, indent=2, ensure_ascii=False)

        print(f"\n--------------------------------------------------")
        print(f"📄 PAGE {i} PERFORMANCE & RESULTS (Saved to: {out_file})")
        print(f"--------------------------------------------------")
        print(f"Dimensions: {page.width}x{page.height}")
        print(f"Page Confidence: {page.confidence}")
        print(f"Sections Count: {len(page.sections)}")
        total_q = sum(len(s.questions) for s in page.sections)
        print(f"Total Questions Detected: {total_q}")

        for s in page.sections:
            s_id = s.section_id or "Main"
            print(f"  Section [{s_id}] - {s.title or 'No Title'}")
            for q in s.questions:
                print(f"    - Q{q.question_no or q.question_id or '?'}: {q.prompt} (Type: {q.type}, Areas: {len(q.answer_areas)})")

    doc_out = os.path.join(output_dir, "full_document_response.json")
    print(f"\nFull Document JSON saved to: {doc_out}")
    with open(doc_out, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
