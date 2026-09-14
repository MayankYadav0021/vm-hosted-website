import csv, os
from app.config import MODEL_PRIMARY, MODEL_2, MODEL_3
from app.services.evaluation_service import EvaluationService

models = [MODEL_PRIMARY, MODEL_2, MODEL_3]
rows = EvaluationService().evaluate(models)
os.makedirs("results", exist_ok=True)
with open("results/model_comparison.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print("Saved results/model_comparison.csv")
