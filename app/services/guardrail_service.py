import re
from pydantic import BaseModel, Field, ValidationError


class GuardrailInput(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class GuardrailOutput(BaseModel):
    answer: str = Field(min_length=1, max_length=5000)


class GuardrailService:

    BLOCKED_PATTERNS = [
        r"ignore previous instructions",
        r"ignore all previous instructions",
        r"disregard previous instructions",
        r"system prompt",
        r"reveal your instructions",
        r"jailbreak",
    ]

    def validate_input(self, question: str):
        try:
            data = GuardrailInput(question=question.strip())
        except ValidationError as e:
            return {
                "allowed": False,
                "reason": "Invalid input",
                "details": str(e)
            }

        lowered = data.question.lower()

        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, lowered):
                return {
                    "allowed": False,
                    "reason": "Blocked prompt pattern detected",
                    "details": pattern
                }

        return {
            "allowed": True,
            "reason": "Input passed guardrails",
            "question": data.question
        }

    def validate_output(self, answer: str):
        try:
            data = GuardrailOutput(answer=answer.strip())
        except ValidationError as e:
            return {
                "allowed": False,
                "reason": "Invalid model output",
                "details": str(e)
            }

        return {
            "allowed": True,
            "reason": "Output passed guardrails",
            "answer": data.answer
        }
