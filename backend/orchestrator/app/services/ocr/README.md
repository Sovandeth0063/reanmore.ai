# Homework OCR + VLM System

Multimodal homework processing pipeline — Phase 1 MVP.

## What it does

Accepts a **photo or PDF** of a student's homework worksheet and returns a **structured JSON representation** that preserves:
- Question numbers and section labels (exact, not renumbered)
- Text, figures, diagrams, tables
- Answer areas (blank lines, boxes, checkboxes)
- Student handwritten answers
- Spatial relationships and reading order

## Architecture

```
Photo / PDF
    ↓
1. Image Preprocessing     (OpenCV: perspective, deskew, shadow, CLAHE, denoise)
    ↓
2. Layout Detection        (PaddleOCR PP-Structure)
    ↓
3. OCR                     (PaddleOCR)
    ↓
4. Visual Processing       (crop figures → base64 for VLM)
    ↓
5. VLM Analysis            (Gemini Vision)
    ↓
6. Structured Homework JSON (Pydantic schemas)
    ↓
7. Validation              (confidence + math + structure checks)
    ↓
8. API Response            (FastAPI)
```

## Project Structure

```
app/
├── main.py                  # FastAPI app
├── config.py                # Settings (from .env)
├── api/routes.py            # POST /process-homework, GET /health
├── schemas/homework.py      # Pydantic output models
├── pipeline/processor.py    # Pipeline orchestrator
├── preprocessing/image_prep.py
├── layout/layout_detector.py
├── ocr/ocr_engine.py
├── vision/visual_processor.py
├── vlm/
│   ├── base.py              # Abstract VLMProvider interface
│   └── gemini_vlm.py        # Gemini Vision implementation
├── validation/validator.py
└── utils/
    ├── pdf_utils.py
    └── image_utils.py
tests/
└── test_pipeline.py
```

## Setup

```bash
# 1. Create virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# 4. Run
python run.py
# or
uvicorn app.main:app --reload --port 9003
```

## API

### `GET /health`
```json
{"status": "ok", "service": "homework-ocr-vlm", "version": "1.0.0"}
```

### `POST /process-homework`

Upload a homework image or PDF:

```bash
curl -X POST http://localhost:9003/process-homework \
  -F "file=@homework.jpg"
```

Query params:
- `debug_crops=true` — save cropped figure regions to `sample_outputs/`

Response (abbreviated):
```json
{
  "status": "success",
  "document": {"title": "Homework 11", "language": ["English"], "pages": 1},
  "pages": [
    {
      "page_number": 1,
      "sections": [
        {
          "section_id": "A",
          "questions": [
            {
              "question_no": "1",
              "type": "fill_blank",
              "prompt": "What is a mammal?",
              "elements": [...],
              "confidence": 0.91
            }
          ]
        }
      ]
    }
  ],
  "confidence": 0.89,
  "warnings": [],
  "processing_time_seconds": 12.4
}
```

Interactive docs: http://localhost:9003/docs

## Configuration (`.env`)

| Key | Default | Description |
|-----|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `VLM_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `MAX_IMAGE_LONG_SIDE` | `2000` | Max px for preprocessing resize |
| `OCR_CONFIDENCE_THRESHOLD` | `0.70` | Below this → flag for review |
| `LOW_CONFIDENCE_THRESHOLD` | `0.60` | Below this → validation warning |
| `ENABLE_KHMER` | `false` | Khmer OCR (Phase 2) |
| `DEBUG` | `false` | Enable debug logging + hot-reload |

## Running Tests

```bash
# Unit tests only (no models needed)
venv\Scripts\python -m pytest tests/ -v -k "not Integration"

# All tests including PDF integration
venv\Scripts\python -m pytest tests/ -v
```

## Swapping VLM provider

1. Create a new class in `app/vlm/` that inherits `VLMProvider`
2. Implement `analyze_page()` and `describe_figure()`
3. Set `VLM_PROVIDER=your_provider` in `.env`
4. Update `_build_vlm()` in `pipeline/processor.py`

## Phase Roadmap

| Phase | Status | Features |
|-------|--------|---------|
| 1 | ✅ MVP | Upload, preprocess, OCR, layout, VLM, JSON, API |
| 2 | ⬜ | Handwriting, math recognition, tables, checkboxes, blank detection |
| 3 | ⬜ | Matching lines, worksheet templates, advanced validation |
