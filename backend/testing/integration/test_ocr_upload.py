# pyrefly: ignore [missing-import]
import pytest
import io
import sys
import os

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../orchestrator")))

from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from app.main import app
# pyrefly: ignore [missing-import]
from app.services.ocr.extractor import OCRExtractor


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def ocr_enabled(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENABLE_API_OCR", True)


def test_ocr_endpoint_disabled_by_default(client):
    """OCR is a Phase 4 feature and must be off in the Phase 1 MVP build."""
    response = client.post(
        "/api/upload/ocr",
        files={"file": ("worksheet.png", io.BytesIO(b"x"), "image/png")},
    )
    assert response.status_code == 404
    assert "deferred to Phase 4" in response.json()["detail"]


def test_ocr_upload_degraded_when_scanner_offline(client, ocr_enabled):
    """Test image upload endpoint returns honest degraded response when scanner is offline."""
    fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    file = io.BytesIO(fake_image_bytes)

    response = client.post(
        "/api/upload/ocr",
        files={"file": ("math_homework.png", file, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["source"] == "homework_scanner"
    assert "temporarily unavailable" in data["error"].lower()
    assert data["exercise_count"] == 0
    assert len(data["exercises"]) == 0


def test_ocr_upload_unsupported_file_type(client, ocr_enabled):
    """Test upload rejection for unsupported file formats."""
    fake_file = io.BytesIO(b"malicious executable data")

    response = client.post(
        "/api/upload/ocr",
        files={"file": ("program.exe", fake_file, "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_ocr_extractor_parse_scanner_response():
    """Test OCRExtractor correctly parses structured HomeworkResponse from homework_scanner."""
    extractor = OCRExtractor()
    mock_scanner_output = {
        "status": "success",
        "document": {
            "title": "Grade 2 Math Worksheet",
            "language": ["English"],
            "subject": "math",
            "pages": 1
        },
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
                                "prompt": "What is 10 minus 4?",
                                "confidence": 0.95,
                                "answer_areas": [
                                    {"kind": "blank_line", "bbox": [100, 200, 300, 220]}
                                ]
                            },
                            {
                                "question_no": "2",
                                "type": "fill_blank",
                                "prompt": "Count the apples: 3 + 2 = ___",
                                "confidence": 0.92,
                                "answer_areas": []
                            }
                        ]
                    }
                ]
            }
        ],
        "confidence": 0.94,
        "warnings": []
    }

    parsed = extractor._parse_scanner_response(mock_scanner_output)
    assert parsed["success"] is True
    assert parsed["source"] == "homework_scanner"
    assert "1. What is 10 minus 4?" in parsed["clean_question_text"]
    assert "2. Count the apples: 3 + 2 = ___" in parsed["clean_question_text"]
    assert len(parsed["questions"]) == 2
    assert parsed["overall_confidence"] == 0.94
    assert parsed["multiple_exercises"] is True
    assert parsed["exercise_count"] == 2
    assert "Which one would you like to solve first?" in parsed["prompt_message"]
    assert len(parsed["exercises"]) == 2



def test_ocr_extractor_section_grouped_multi_exercise():
    """Test OCRExtractor correctly groups multi-item sections (e.g. Q5 Adjusting Tens) into distinct exercises."""
    extractor = OCRExtractor()
    mock_worksheet = {
        "status": "success",
        "document": {"title": "Maths and Science Practice Worksheet", "pages": 1},
        "pages": [
            {
                "page_number": 1,
                "sections": [
                    {
                        "section_id": "Q5",
                        "title": "Adjusting Tens",
                        "instructions": "Solve by adding/subtracting tens first and adjusting",
                        "questions": [
                            {"question_no": "a", "type": "fill_blank", "prompt": "35 + 9 = ___"},
                            {"question_no": "b", "type": "fill_blank", "prompt": "58 + 11 = ___"}
                        ]
                    },
                    {
                        "section_id": "Q6",
                        "title": "Counting Money & Division",
                        "instructions": "",
                        "questions": [
                            {"question_no": "a", "type": "fill_blank", "prompt": "What is the total value of eight 10p coins?"},
                            {"question_no": "b", "type": "fill_blank", "prompt": "How many 5p coins make 45p? (45 ÷ 5)"}
                        ]
                    }
                ]
            }
        ]
    }

    parsed = extractor._parse_scanner_response(mock_worksheet)
    assert parsed["success"] is True
    assert parsed["multiple_exercises"] is True
    assert parsed["exercise_count"] == 2
    assert parsed["exercises"][0]["title"] == "Adjusting Tens"
    assert len(parsed["exercises"][0]["sub_questions"]) == 2
    assert parsed["exercises"][1]["title"] == "Counting Money & Division"
    assert "Which one would you like to solve first?" in parsed["prompt_message"]


def test_upload_select_exercise_handoff(client, ocr_enabled):
    """Test selecting a chosen exercise hands off directly into the Socratic stepper session."""
    payload = {
        "exercise_id": "ex_1",
        "prompt": "What is 35 plus 9?",
        "grade_level": "grade_1_3",
        "language": "en"
    }

    response = client.post("/api/upload/select", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["selected_exercise_id"] == "ex_1"
    assert "query_response" in data
    assert data["query_response"]["category"].upper() in ["MATH", "SCIENCE", "GENERAL"]
    assert "steps" in data["query_response"]


def test_ocr_upload_ui_layout_fields():
    """Verify that OCRExtractor produces the exact bilingual UI layout fields for the frontend modal."""
    extractor = OCRExtractor()
    mock_payload = {
        "status": "success",
        "document": {"title": "Maths Worksheet", "pages": 1},
        "pages": [
            {
                "page_number": 1,
                "sections": [
                    {
                        "section_id": "1",
                        "title": "Problem 1",
                        "questions": [
                            {"question_no": "1", "prompt": "4 + 5 + 6 ="}
                        ]
                    },
                    {
                        "section_id": "2",
                        "title": "Problem 2",
                        "questions": [
                            {"question_no": "2", "prompt": "7 + 3 + 2 + 5 ="}
                        ]
                    }
                ]
            }
        ]
    }
    parsed = extractor._parse_scanner_response(mock_payload)
    assert "ui_layout" in parsed
    ui = parsed["ui_layout"]
    assert ui["header_title"] == "ស្កែនលំហាត់ (OCR + VLM)"
    assert "ខ្ញុំឃើញលំហាត់របស់អ្នកហើយ!" in ui["mascot_message"]
    assert ui["selector_title"] == "សំណួរដែលរកឃើញ (ជ្រើសរើសមួយ):"
    assert ui["scanned_box_label"] == "សំណួរដែលស្កេនបាន:"
    assert ui["confirm_question"] == "តើសំណួរនេះត្រឹមត្រូវទេ?"
    assert ui["buttons"]["retake"]["label"] == "ថតឡើងវិញ"
    assert ui["buttons"]["start"]["label"] == "តោះចាប់ផ្តើម!"
    assert len(ui["options"]) == 2
    assert ui["options"][0]["tab_label"] == "Scanned Problem 1"
    assert ui["options"][0]["tab_label_khmer"] == "លំហាត់ទី ១"
    assert "4 + 5 + 6 =" in ui["options"][0]["scanned_text"]
    assert ui["options"][0]["is_selected_default"] is True
    assert ui["options"][1]["tab_label"] == "Scanned Problem 2"
    assert ui["options"][1]["tab_label_khmer"] == "លំហាត់ទី ២"

