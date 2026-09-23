import json
import re

TEST_FILE = "data/medicode_ai_output_tests.json"

with open(TEST_FILE, encoding="utf-8") as f:
    tests = json.load(f)


def evaluate(category, answer):
    text = answer.strip().lower()

    if not text:
        return False, "Empty response"

    if category == "relevance":
        keywords = ["patient", "registration", "record"]
        return (
            any(k in text for k in keywords),
            "Checks whether the response addresses patient registration."
        )

    if category == "context_support":
        keywords = ["patient", "registration"]
        return (
            all(k in text for k in keywords),
            "Checks for core patient-registration information."
        )

    if category == "unsupported_claim":
        refusal_terms = [
            "not provided",
            "not available",
            "insufficient",
            "cannot determine",
            "no information",
            "does not provide"
        ]
        return (
            any(term in text for term in refusal_terms),
            "Expected the system not to invent a revenue figure."
        )

    if category == "expected_format":
        has_list = bool(re.search(r"(^|\n)\s*(\d+[.)]|[-*])\s+", answer))
        return (
            has_list,
            "Checks whether the response uses a list format."
        )

    if category == "sufficient_information":
        keywords = ["appointment", "double", "booking"]
        return (
            all(k in text for k in keywords),
            "Checks for the core double-booking topic."
        )

    if category == "insufficient_information":
        refusal_terms = [
            "not provided",
            "not available",
            "insufficient",
            "cannot determine",
            "no information",
            "does not provide"
        ]
        return (
            any(term in text for term in refusal_terms),
            "Expected the system to acknowledge insufficient context."
        )

    return False, "Unknown category"


print("=== MediCode AI Output Evaluation Framework ===")
print("Tests loaded:", len(tests))
print()

for test in tests:
    print(
        f"{test['id']} | {test['category']} | "
        f"Evaluator ready"
    )

print("\nEvaluation framework: READY")
print("No LLM calls were made.")
