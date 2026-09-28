"""
File: testing/test_cases.py
Description: Automated integration test suite. Sends pre-configured test queries
             covering different subjects and grade levels to evaluate Orchestrator output.
             Requires zero dependencies (uses Python's standard urllib).
"""

import os
import sys
import json
import urllib.request
import urllib.error
import uuid

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

GATEWAY_URL = "http://localhost:9000/api/query"

TEST_CASES = [
    {
        "name": "Math Equation (Grade 4-6 Level)",
        "query": "solve 2*x + 4 = 10",
        "grade_level": "grade_4_6",
        "expected_subject": "MATH"
    },
    {
        "name": "Math Word Problem (Grade 1-3 Level)",
        "query": "If Lily has 10 marbles and gives 4 to Sam, how many marbles does Lily have left?",
        "grade_level": "grade_1_3",
        "expected_subject": "MATH"
    },
    {
        "name": "General Science Question (Elementary Level)",
        "query": "Why do plants have green leaves?",
        "grade_level": "grade_4_6",
        "expected_subject": "GENERAL"
    }
]

def run_test(test: dict) -> bool:
    print(f"\nRunning: {test['name']}")
    print(f"Query:   '{test['query']}'")
    print(f"Grade:   {test['grade_level']}")
    
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    data = {
        "query": test["query"],
        "session_id": session_id,
        "grade_level": test["grade_level"]
    }
    json_data = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(
        GATEWAY_URL,
        data=json_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                res_payload = json.loads(response.read().decode("utf-8"))
                
                actual_subject = res_payload.get("category")
                solution = res_payload.get("solution")
                steps_count = len(res_payload.get("steps", []))
                
                print(f"Result:  Success! Classified Category: {actual_subject}")
                print(f"Steps:   Compiled {steps_count} hidden solving steps.")
                print(f"Feedback Preview:\n  \"{solution[:100]}...\"")
                
                if actual_subject != test["expected_subject"]:
                    print(f"  [FAIL] Expected subject {test['expected_subject']} but got {actual_subject}")
                    return False
                return True
    except urllib.error.URLError as e:
        print(f"  [ERROR] Cannot connect to Orchestrator at {GATEWAY_URL}. Is Docker running?")
        return False
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        return False

def main():
    print("==================================================")
    print("       AUTOMATED GATEWAY INTEGRATION TESTS        ")
    print("==================================================")
    
    success_count = 0
    for idx, test in enumerate(TEST_CASES):
        print(f"\n--- TEST CASE {idx+1}/{len(TEST_CASES)} ---")
        if run_test(test):
            success_count += 1
            
    print("\n==================================================")
    print(f"Test Summary: {success_count}/{len(TEST_CASES)} passed.")
    print("==================================================")


# Pytest compatibility wrapper
try:
    # pyrefly: ignore [missing-import]
    import pytest
    # pyrefly: ignore [missing-import]
    from app.services.socratic.graph import socratic_graph

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    async def test_case_execution(case):
        config = {"configurable": {"thread_id": f"pytest_{uuid.uuid4().hex[:6]}"}}
        result = await socratic_graph.ainvoke(
            {
                "raw_user_input": case["query"],
                "grade_level": case["grade_level"],
                "detected_intent": "INITIAL_QUESTION"
            },
            config=config
        )
        assert result is not None
        assert result.get("formatted_markdown") is not None
except ImportError:
    pass

if __name__ == "__main__":
    main()
