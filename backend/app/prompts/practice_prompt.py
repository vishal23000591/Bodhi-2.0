from app.prompts.language import DEFAULT_LANGUAGE, language_instruction

PRACTICE_GENERATION_PROMPT = """You are Bodhi, a tutor. Using ONLY the
textbook excerpts for this topic, generate a practice set:
- 5 multiple-choice questions (MCQs), each with exactly 4 options and one
  correct_index (0-3). If a known misconception is given below, make one
  MCQ's wrong option target that misconception directly and set
  distractor_note explaining it; otherwise omit distractor_note.
- 2 short-answer questions (open-ended, answerable in 1-3 sentences from the
  excerpts).

Return STRICT JSON in this exact shape:
{
  "mcqs": [{"question": "...", "options": ["...", "...", "...", "..."], "correct_index": 0, "distractor_note": "..."}],
  "short_answers": [{"question": "..."}]
}"""

SHORT_ANSWER_SCORING_PROMPT = """You are grading a student's short answer
against textbook excerpts. Score 0-100 for how well it demonstrates correct
understanding of the underlying concept — NOT for how closely it matches
the textbook's wording. A student who explains the idea correctly in their
own words, with different examples, phrasing, or detail than the excerpts,
should score just as well as one who echoes the textbook. Only mark it down
for being scientifically wrong, missing the key idea, or not answering the
question — never for phrasing it differently. Give a one-sentence
explanation, especially if it's wrong or incomplete.

Return STRICT JSON: {"score": <0-100>, "explanation": "..."}"""


def build_generation_messages(
    topic_title: str,
    context: str,
    misconceptions: list[dict],
    language: str = DEFAULT_LANGUAGE,
) -> list[dict[str, str]]:
    misconception_note = ""
    if misconceptions:
        top = misconceptions[0]
        misconception_note = (
            f"\n\nKNOWN MISCONCEPTION TO TARGET: student said '{top.get('claim')}'; "
            f"correction: '{top.get('correction')}'."
        )
    return [
        {"role": "system", "content": PRACTICE_GENERATION_PROMPT + language_instruction(language)},
        {"role": "user", "content": f"TOPIC: {topic_title}\n\nTEXTBOOK EXCERPTS:\n{context}{misconception_note}"},
    ]


def build_short_answer_scoring_messages(
    question: str, context: str, student_answer: str, language: str = DEFAULT_LANGUAGE
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SHORT_ANSWER_SCORING_PROMPT + language_instruction(language)},
        {
            "role": "user",
            "content": f"QUESTION: {question}\n\nTEXTBOOK EXCERPTS:\n{context}\n\nSTUDENT'S ANSWER:\n{student_answer}",
        },
    ]
