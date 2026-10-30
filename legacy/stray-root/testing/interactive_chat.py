"""
File: testing/interactive_chat.py
Description: Interactive terminal-based Socratic tutor test client. 
             Connects to the Orchestrator Gateway at http://localhost:9000/api/query.
             Requires zero dependencies (uses Python's standard urllib).
"""

import json
import urllib.request
import urllib.error
import uuid
import sys

# Color codes for terminal beauty
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

GATEWAY_URL = "http://localhost:9000/api/query"

def send_query(query: str, session_id: str, grade_level: str, language: str) -> dict:
    """
    Sends the user query or student step attempt to the Orchestrator gateway.
    """
    data = {
        "query": query,
        "session_id": session_id,
        "grade_level": grade_level,
        "language": language
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
                return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"\n{RED}{BOLD}[ERROR]{RESET} Cannot connect to Orchestrator Gateway at http://localhost:9000.")
        print("Please make sure your docker containers are running (`docker compose up`).")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}{BOLD}[ERROR]{RESET} Failed to process request: {e}")
        sys.exit(1)

def main():
    print(f"{BLUE}{BOLD}==================================================")
    print("      SOCRATIC TUTOR INTERACTIVE CLI CLIENT       ")
    print(f"=================================================={RESET}\n")

    # 1. Choose Language
    print(f"{BOLD}Select Preferred Language:{RESET}")
    print("1. English [Default]")
    print("2. Khmer")
    lang_choice = input("\nEnter choice (1-2): ").strip()
    language = "khmer" if lang_choice == "2" else "en"
    print(f"\n{GREEN}Selected Language: {language.upper()}{RESET}\n")

    # 2. Choose Grade Level
    print(f"{BOLD}Select Student Grade Level:{RESET}")
    print("1. Grade 1-3 (Elementary)")
    print("2. Grade 4-6 (Upper Primary)")
    print("3. Grade 7-9 (Secondary)")
    print("4. Grade 10-12 (High School) [Default]")
    
    choice = input("\nEnter choice (1-4): ").strip()
    grade_map = {
        "1": "grade_1_3",
        "2": "grade_4_6",
        "3": "grade_7_9",
        "4": "grade_10_12"
    }
    grade_level = grade_map.get(choice, "grade_10_12")
    print(f"\n{GREEN}Selected Grade Level: {grade_level}{RESET}\n")

    # 3. Enter initial math/science exercise
    session_id = f"cli_{uuid.uuid4().hex[:8]}"
    print(f"{BOLD}Enter the science exercise or question you want to solve:{RESET}")
    if language == "khmer":
        print("Example: ដោះស្រាយសមីការ 3*x + 9 = 18")
    else:
        print("Example: solve 3*x + 9 = 18")
        
    initial_query = input("\nQuestion: ").strip()
    if not initial_query:
        print("Empty question. Exiting.")
        sys.exit(0)

    print(f"\n{YELLOW}Initializing Socratic session with Gateway...{RESET}")
    response = send_query(initial_query, session_id, grade_level, language)

    # 4. Chat loop
    while True:
        category = response.get("category", "GENERAL")
        solution = response.get("solution", "")
        steps = response.get("steps", [])
        step_idx = response.get("current_step_index", 0)
        hint_count = response.get("hint_count", 0)
        practice_mode = response.get("practice_mode", False)

        print(f"\n{BLUE}{BOLD}--- TUTOR RESPONSE ---{RESET}")
        print(f"{BOLD}Subject Category:{RESET} {category}")
        if practice_mode:
            print(f"{BOLD}Mode:{RESET} Practice Problem")
        print(f"{BOLD}Tutor Feedback:{RESET}\n{GREEN}{solution}{RESET}")
        print(f"{BLUE}{BOLD}----------------------{RESET}")

        # Show debugging/telemetry metrics
        debug_info = f"[Step Index: {step_idx}/{len(steps)} | Mistakes: {hint_count}]"
        print(f"{YELLOW}{debug_info}{RESET}")

        # Prompt student for their attempt
        student_input = input(f"\n{BOLD}Your Step / Answer (or type 'exit' to quit): {RESET}").strip()
        if not student_input:
            continue
        if student_input.lower() in ["exit", "quit", "q"]:
            print(f"\n{BLUE}Goodbye! Keep learning!{RESET}")
            break

        print(f"\n{YELLOW}Sending step attempt...{RESET}")
        response = send_query(student_input, session_id, grade_level, language)

if __name__ == "__main__":
    main()
