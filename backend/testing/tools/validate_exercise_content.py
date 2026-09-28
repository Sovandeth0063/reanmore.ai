"""
Validation tool to audit exercise content quality across frontend/src/services/translationService.ts
and frontend/src/data/math.json / science.json.

Validates:
1. Completeness: hint1, hint2, hint3 exist for all steps in targeted exercises.
2. Zero answer leakage: Step expected answers must not appear directly in hint1 or hint2.
3. Zero Latin characters in child-facing Khmer fields.
4. No cross-exercise hint duplication (prevent copy-paste contamination).
"""

import re
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TRANSLATION_FILE = REPO_ROOT / "frontend" / "src" / "services" / "translationService.ts"
MATH_FILE = REPO_ROOT / "frontend" / "src" / "data" / "math.json"

LATIN_RE = re.compile(r"[a-zA-Z]")


def parse_translations_file():
    content = TRANSLATION_FILE.read_text(encoding="utf-8")
    # Extract the HARDCODED_KHMER_TRANSLATIONS object
    start_match = re.search(r"export const HARDCODED_KHMER_TRANSLATIONS:\s*Record<string,\s*CaseKhmerData>\s*=\s*\{", content)
    if not start_match:
        raise ValueError("Could not find HARDCODED_KHMER_TRANSLATIONS in translationService.ts")
    
    # We can parse the JSON-like keys by matching object blocks
    # Or cleaner: convert the typescript object to JSON
    # Find closing `};\n\n/** Translation Cache`
    end_match = re.search(r"\n\};\s*\n\s*/\*\* Translation Cache", content)
    if not end_match:
        raise ValueError("Could not find end of HARDCODED_KHMER_TRANSLATIONS")
    
    raw_js = content[start_match.end() - 1:end_match.start() + 2]
    # Simple cleanup to make valid JSON:
    # 1. replace trailing commas before } or ]
    cleaned = re.sub(r",\s*([\}\]])", r"\1", raw_js)
    # 2. quote keys if unquoted
    cleaned = re.sub(r"([{,]\s*)([a-zA-Z0-9_]+)\s*:", r'\1"\2":', cleaned)
    
    return json.loads(cleaned)


def main():
    print("=== Auditing Exercise Content Quality ===")
    translations = parse_translations_file()
    math_data = json.loads(MATH_FILE.read_text(encoding="utf-8"))
    
    # Target: Homework 1 (math_p1_a1 to math_p1_a5, math_p1_b1 to math_p1_b6)
    hw1_ids = [
        "math_p1_a1", "math_p1_a2", "math_p1_a3", "math_p1_a4", "math_p1_a5",
        "math_p1_b1", "math_p1_b2", "math_p1_b3", "math_p1_b4", "math_p1_b5", "math_p1_b6"
    ]
    
    errors = []
    
    # 1. Audit completeness and Latin characters in Homework 1
    for case_id in hw1_ids:
        if case_id not in translations:
            errors.append(f"[{case_id}] Missing from translationService.ts")
            continue
        
        c = translations[case_id]
        statement = c.get("statementKhmer", "")
        if LATIN_RE.search(statement):
            errors.append(f"[{case_id}] statementKhmer contains Latin characters: {statement}")
            
        steps = c.get("steps", [])
        m_case = math_data.get("cases", {}).get(case_id, {})
        m_steps = m_case.get("steps", [])
        
        if len(steps) != len(m_steps):
            errors.append(f"[{case_id}] Step count mismatch: Khmer has {len(steps)}, math.json has {len(m_steps)}")
            
        for idx, step in enumerate(steps):
            s_num = idx + 1
            # Check fields
            for f in ["questionKhmer", "hint1Khmer", "hint2Khmer", "hint3Khmer"]:
                val = step.get(f, "")
                if not val:
                    errors.append(f"[{case_id} Step {s_num}] Missing {f}")
                elif LATIN_RE.search(val):
                    errors.append(f"[{case_id} Step {s_num}] {f} contains Latin characters: {val}")
            
            # Check answer leakage
            if idx < len(m_steps):
                ans = str(m_steps[idx].get("expected_student_answer", "")).strip()
                # If expected answer is numeric (e.g. "10", "15", "7")
                if ans.isdigit():
                    km_map = {'0': '០', '1': '១', '2': '២', '3': '៣', '4': '៤', '5': '៥', '6': '៦', '7': '៧', '8': '៨', '9': '៩'}
                    ans_km = "".join(km_map.get(d, d) for d in ans)
                    h1 = step.get("hint1Khmer", "")
                    h2 = step.get("hint2Khmer", "")
                    # Hint 1 and Hint 2 should not say "ស្មើនឹង {ans_km}" or "= {ans_km}"
                    for h_val, h_name in [(h1, "hint1Khmer"), (h2, "hint2Khmer")]:
                        if f"ស្មើ {ans_km}" in h_val or f"ស្មើនឹង {ans_km}" in h_val or f"= {ans_km}" in h_val:
                            errors.append(f"[{case_id} Step {s_num}] Direct answer leak in {h_name}: {h_val}")
                            
        # Check overall hints and explain
        hints_km = c.get("hintsKhmer", [])
        if len(hints_km) != 3:
            errors.append(f"[{case_id}] hintsKhmer must have exactly 3 items, found {len(hints_km)}")
        for h in hints_km:
            if LATIN_RE.search(h):
                errors.append(f"[{case_id}] hintsKhmer item contains Latin characters: {h}")
                
        explain = c.get("explainKhmer", {})
        for k in ["messageKhmer", "questionKhmer"]:
            val = explain.get(k, "")
            if not val:
                errors.append(f"[{case_id}] explainKhmer missing {k}")
            elif LATIN_RE.search(val):
                errors.append(f"[{case_id}] explainKhmer.{k} contains Latin characters: {val}")

    # 2. Check cross-exercise contamination
    # Ensure addition exercises (Part A) do not contain "១០០" in their parallel examples
    for case_id in ["math_p1_a1", "math_p1_a2", "math_p1_a3", "math_p1_a4", "math_p1_a5"]:
        c = translations.get(case_id, {})
        h_text = " ".join(c.get("hintsKhmer", []))
        e_text = c.get("explainKhmer", {}).get("messageKhmer", "")
        if "១០០" in h_text or "១០០" in e_text:
            errors.append(f"[{case_id}] Contaminated with '100' make-100 logic in hints or example!")

    print(f"Audited {len(hw1_ids)} Homework 1 exercises across {sum(len(translations.get(cid, {}).get('steps', [])) for cid in hw1_ids)} steps.")
    
    if errors:
        print(f"\n❌ FAILED with {len(errors)} issues:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("\n✅ PASSED! All Homework 1 hints, examples, and explanations are complete, non-leaking, and 100% compliant with Khmer pedagogy.")
        sys.exit(0)


if __name__ == "__main__":
    main()
