import csv
import os

from app.config import MODEL_PRIMARY, MODEL_2, MODEL_3
from app.services.evaluation_service import EvaluationService


# Evaluate the three models required for Week 4.
# If one model fails, EvaluationService records the failure
# and continues with the remaining models.

models = [
    MODEL_2,
    MODEL_3,
    MODEL_PRIMARY,
]


print("Models to evaluate:")
for model in models:
    print(f" - {model}")

service = EvaluationService()

rows = service.evaluate(models)

os.makedirs("results", exist_ok=True)

output_file = "results/model_comparison.csv"

if rows:
    fieldnames = list(rows[0].keys())

    # Include any additional fields that may appear
    # in later results.
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {output_file}")
    print(f"Total evaluation records: {len(rows)}")

else:
    print("No evaluation results were generated.")
