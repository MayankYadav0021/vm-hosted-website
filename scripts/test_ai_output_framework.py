import json
import re

TEST_FILE = "data/medicode_ai_output_tests.json"

with open(TEST_FILE, encoding="utf-8") as f:
    tests = json.load(f)


def evaluate(category, answer):
    text = answer.strip().lower()

    if not text:
        return False

    if category == "relevance":
        return any(k in text for k in ["patient", "registration", "record"])

    if category == "context_support":
        return "patient" in text and "registration" in text

    if category == "unsupported_claim":
        refusal_terms = [
            "not provided", "not available", "insufficient",
            "cannot determine", "no information", "does not provide"
        ]
        return any(term in text for term in refusal_terms)

    if category == "expected_format":
        return bool(re.search(r"(^|\n)\s*(\d+[.)]|[-*])\s+", answer))

    if category == "sufficient_information":
        return all(k in text for k in ["appointment", "double", "booking"])

    if category == "insufficient_information":
        refusal_terms = [
            "not provided", "not available", "insufficient",
            "cannot determine", "no information", "does not provide"
        ]
        return any(term in text for term in refusal_terms)

    return False


example_answers = {
    "A01": "Patient registration creates a new patient record and collects registration information.",
    "A02": "Patient registration requires patient information and creates the registration record.",
    "A03": "The available MediCore documentation does not provide information about annual revenue.",
    "A04": "1. Collect patient information\n2. Validate the information\n3. Create the patient record",
    "A05": "Appointment Management checks whether the doctor and time slot are already booked to prevent double booking.",
    "A06": "The available documentation does not provide enough information to determine the original programming language."
}

passed = 0

print("=== MediCode AI Output Framework Test ===")

for test in tests:
    answer = example_answers[test["id"]]
    result = evaluate(test["category"], answer)
    status = "PASS" if result else "FAIL"

    if result:
        passed += 1

    print(f"{test['id']} | {test['category']} | {status}")

print(f"\nPassed: {passed}/{len(tests)}")
print(f"Framework accuracy: {passed / len(tests) * 100:.1f}%")
print("\nNote: These are controlled test responses, not LLM evaluation results.")
