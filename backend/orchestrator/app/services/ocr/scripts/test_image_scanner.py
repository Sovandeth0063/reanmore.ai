"""Utility script to test an image against the Homework Scanner pipeline
and save the structured JSON output into `services/homework_scanner/sample_outputs/`.

Usage:
    python services/homework_scanner/scripts/test_image_scanner.py --image path/to/image.png
    python scripts/test_image_scanner.py --image ../sample_inputs/test1.png  (from inside services/homework_scanner/)
"""

import os
import sys
import json
import time
import argparse

# Force UTF-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Configure service and repository root paths
script_dir = os.path.dirname(os.path.abspath(__file__))
hw_scanner_dir = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, hw_scanner_dir)

# Ensure environment variables are loaded from services/homework_scanner/.env
from dotenv import load_dotenv
load_dotenv(os.path.join(hw_scanner_dir, ".env"), override=True)

# pyrefly: ignore [missing-import]
from app.services.ocr.pipeline.processor import HomeworkProcessor


def main():
    parser = argparse.ArgumentParser(description="Test image input with Homework Scanner and save JSON output.")
    parser.add_argument("--image", "-i", required=True, help="Path to input image (PNG, JPG, etc.)")
    parser.add_argument("--output", "-o", default=None, help="Custom output JSON path (defaults to sample_outputs/<name>_output.json)")
    args = parser.parse_args()

    image_path = os.path.abspath(args.image)
    if not os.path.exists(image_path):
        # Also check relative to script_dir and sample_inputs
        rel_to_script = os.path.join(script_dir, args.image)
        rel_to_inputs = os.path.join(hw_scanner_dir, "sample_inputs", args.image)
        if os.path.exists(rel_to_script):
            image_path = rel_to_script
        elif os.path.exists(rel_to_inputs):
            image_path = rel_to_inputs
        else:
            print(f"❌ Error: File not found: {args.image}")
            sys.exit(1)

    # Determine output file path (defaults to sample_outputs/)
    output_dir = os.path.join(hw_scanner_dir, "sample_outputs")
    os.makedirs(output_dir, exist_ok=True)

    if args.output:
        output_file = os.path.abspath(args.output)
    else:
        stem = os.path.splitext(os.path.basename(image_path))[0]
        output_file = os.path.join(output_dir, f"{stem}_output.json")

    print("=" * 60)
    print(f"📷 Testing Image: {image_path}")
    print(f"📁 Output Destination: {output_file}")
    print("=" * 60)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"Image Size: {len(image_bytes) / 1024:.1f} KB")

    # Initialize processor
    print("Initializing HomeworkProcessor...")
    processor = HomeworkProcessor()
    print(f"Active VLM Provider: {type(processor._vlm).__name__}")
    if hasattr(processor._vlm, "_model_name"):
        print(f"Active VLM Model: {processor._vlm._model_name}")
    if hasattr(processor._vlm, "_base_url"):
        print(f"Active Base URL: {processor._vlm._base_url}")

    t_start = time.perf_counter()
    print("\nProcessing image through pipeline...")
    response = processor.process(file_bytes=image_bytes, filename=os.path.basename(image_path))
    duration = time.perf_counter() - t_start

    print(f"\n✅ Completed in {duration:.2f}s!")
    print(f"Overall Confidence: {response.confidence}")
    print(f"Stage Timers: {response.stage_timers}")

    # Save complete JSON
    result_dict = response.model_dump(exclude_none=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved structured JSON to: {output_file}")

    # Display extracted questions summary
    for page in response.pages:
        for section in page.sections:
            sec_name = section.title or section.section_id or "Section"
            print(f"\n📌 {sec_name}")
            for q in section.questions:
                q_num = q.question_no or q.question_id or "?"
                sub_count = len(q.sub_questions) if hasattr(q, "sub_questions") else 0
                sub_text = f" ({sub_count} sub-questions)" if sub_count else ""
                print(f"   • {q_num}: {q.prompt}{sub_text}")


if __name__ == "__main__":
    main()
