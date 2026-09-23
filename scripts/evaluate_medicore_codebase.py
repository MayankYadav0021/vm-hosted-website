import json
from pathlib import Path

with open("data/medicode_codebase_questions.json", encoding="utf-8") as f:
    questions = json.load(f)

ROOT = Path(".")

checks = {
    "CB01": ["book_appointment", "Doctor already has an appointment"],
    "CB02": ["PatientService", "register_patient"],
    "CB03": ["PatientService", "Patient", "register_patient"],
    "CB04": ["mark_paid", "Invoice not found"],
    "CB05": ["ROLE_PERMISSIONS", "doctor", "billing"],
    "CB06": ["authenticate", "authorize", "doctor"],
    "CB07": ["Patient already exists"],
    "CB08": ["class AppointmentService", "self.appointments"],
}

passed = 0

print("=== MediCore Codebase Evaluation ===")

for item in questions:
    question_id = item["id"]
    expected_files = item["expected_files"]
    required_terms = checks[question_id]

    combined_text = ""

    for file_name in expected_files:
        path = ROOT / file_name

        if not path.exists():
            continue

        combined_text += path.read_text(encoding="utf-8") + "\n"

    missing_terms = [
        term for term in required_terms
        if term not in combined_text
    ]

    success = not missing_terms

    if success:
        passed += 1

    print(
        f"{question_id} | "
        f"{'PASS' if success else 'FAIL'} | "
        f"Expected files: {len(expected_files)}"
    )

    if missing_terms:
        print(f"  Missing terms: {missing_terms}")

print("\n=== SUMMARY ===")
print(f"Passed: {passed}/{len(questions)}")
print(f"Codebase verification: {passed / len(questions) * 100:.1f}%")
