from pydantic import BaseModel


class MCQOut(BaseModel):
    question: str
    options: list[str]


class ShortAnswerOut(BaseModel):
    question: str


class PracticeSetOut(BaseModel):
    id: str
    mcqs: list[MCQOut]
    short_answers: list[ShortAnswerOut]


class PracticeSubmitRequest(BaseModel):
    mcq_answers: list[int]
    short_answers: list[str]


class PracticeResultOut(BaseModel):
    mcq_score: str
    mcq_correct_indices: list[int]
    short_answer_scores: list[int]
    short_answer_explanations: list[str]
    overall_score: int
