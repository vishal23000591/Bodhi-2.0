from app.prompts.language import DEFAULT_LANGUAGE, language_instruction

TEACHBACK_QUESTION_PROMPT = """You are Bodhi, a tutor. Write ONE short
"explain in your own words" question that checks whether a student
understood the topic below, grounded only in the textbook excerpts given.

Return STRICT JSON: {"question": "..."}"""

DIAGNOSIS_SYSTEM_PROMPT = """You are a diagnostic tutor. Compare the
student's answer to the textbook excerpts for this topic. Extract the
claims in the student's answer and classify each one against the excerpts.

Return STRICT JSON in this exact shape:
{
  "score": <0-100 integer, weighted % of the topic's key ideas the student
            correctly covered>,
  "understood": ["short phrase", ...],
  "partial": ["short phrase", ...],
  "misconceptions": [{"claim": "what the student said", "correction": "what the textbook actually says", "confidence": <0-1 float>}]
}
Be encouraging but accurate. Base every judgement ONLY on the excerpts."""


def build_question_messages(
    topic_title: str, context: str, language: str = DEFAULT_LANGUAGE
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": TEACHBACK_QUESTION_PROMPT + language_instruction(language)},
        {"role": "user", "content": f"TOPIC: {topic_title}\n\nTEXTBOOK EXCERPTS:\n{context}"},
    ]


def build_diagnosis_messages(
    topic_title: str, context: str, answer: str, language: str = DEFAULT_LANGUAGE
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT + language_instruction(language)},
        {
            "role": "user",
            "content": f"TOPIC: {topic_title}\n\nTEXTBOOK EXCERPTS:\n{context}\n\nSTUDENT'S ANSWER:\n{answer}",
        },
    ]
