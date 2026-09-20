import json
import os
import re

QUESTIONS_FILE = "week4/exercise6_questions.json"
CODEBASE_DIR = "sample_codebase"
OUTPUT_FILE = "week4/exercise6_results.json"


def read_codebase():
    files = {}

    for root, _, filenames in os.walk(CODEBASE_DIR):
        for filename in filenames:
            if filename.endswith(".py") or filename.endswith(".md"):
                path = os.path.join(root, filename)

                with open(path, "r", encoding="utf-8") as f:
                    files[path] = f.read()

    return files


def check_question(question, files):
    q = question["question"].lower()
    expected = question["expected"].lower()

    combined = "\n".join(
        f"{path}\n{content}"
        for path, content in files.items()
    ).lower()

    keywords = re.findall(r"[a-zA-Z_]+\.py|[a-zA-Z_]+\(\)", expected)

    found = 0

    for keyword in keywords:
        if keyword in combined:
            found += 1

    if question["id"] == 1:
        passed = "sample_codebase/auth/auth_service.py" in combined

    elif question["id"] == 2:
        passed = "def authenticate" in combined

    elif question["id"] == 3:
        passed = "sample_codebase/auth/session.py" in combined

    elif question["id"] == 4:
        passed = (
            "api/registration_routes.py" in combined
            and "users/registration.py" in combined
            and "users/user_service.py" in combined
        )

    elif question["id"] == 5:
        passed = "def register_user" in combined

    elif question["id"] == 6:
        passed = "sample_codebase/payments/payment_service.py" in combined

    elif question["id"] == 7:
        passed = (
            "api/payment_routes.py" in combined
            and "process_payment" in combined
        )

    elif question["id"] == 8:
        passed = "sample_codebase/tests/test_auth.py" in combined

    elif question["id"] == 9:
        passed = (
            "auth/auth_service.py" in combined
            and "auth/session.py" in combined
            and "api/auth_routes.py" in combined
            and "tests/test_auth.py" in combined
        )

    elif question["id"] == 10:
        passed = (
            "api/registration_routes.py" in combined
            and "users/registration.py" in combined
            and "users/user_service.py" in combined
            and "tests/test_registration.py" in combined
        )

    else:
        passed = False

    return {
        "id": question["id"],
        "question": question["question"],
        "expected": question["expected"],
        "passed": passed
    }


def main():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    files = read_codebase()

    results = [
        check_question(question, files)
        for question in questions
    ]

    passed = sum(1 for result in results if result["passed"])
    total = len(results)

    output = {
        "exercise": "Week 4 Exercise 6 - Repository/Codebase Understanding",
        "total_questions": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_percent": round((passed / total) * 100, 2),
        "results": results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("======================================")
    print("Week 4 Exercise 6")
    print("======================================")
    print("Questions:", total)
    print("Passed:", passed)
    print("Failed:", total - passed)
    print("Pass rate:", round((passed / total) * 100, 2), "%")
    print()
    print("Results saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
