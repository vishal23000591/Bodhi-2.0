from pydantic import BaseModel


class TeachbackQuestionOut(BaseModel):
    question: str


class TeachbackAnswerRequest(BaseModel):
    answer: str
    language: str = "en"


class Misconception(BaseModel):
    claim: str
    correction: str = ""
    confidence: float = 0.0


class TeachbackResultOut(BaseModel):
    score: int
    understood: list[str]
    partial: list[str]
    misconceptions: list[Misconception]


class TeachOut(BaseModel):
    explanation: str
    sources: list[dict]
