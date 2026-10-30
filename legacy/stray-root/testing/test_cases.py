"""
File: testing/test_cases.py
Description: Automated integration test suite. Sends pre-configured test queries
             covering different subjects and grade levels to evaluate Orchestrator output.
             Requires zero dependencies (uses Python's standard urllib).
"""

import json
import urllib.request
import urllib.error
import uuid

GATEWAY_URL = "http://localhost:9000/api/query"

TEST_CASES = [
    {
        "name": "Math Equation (High School Level)",
        "query": "solve 2*x + 4 = 10",
        "grade_level": "grade_10_12",
        "expected_subject": "MATH"
    },
    {
        "name": "Math Word Problem (Elementary Level)",
        "query": "If Lily has 10 marbles and gives 4 to Sam, how many marbles does Lily have left?",
        "grade_level": "grade_1_3",
        "expected_subject": "MATH"
    },
    {
        "name": "General Science Question (Middle School Level)",
        "query": "Why is the sky blue?",
        "grade_level": "grade_7_9",
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

if __name__ == "__main__":
    main()
