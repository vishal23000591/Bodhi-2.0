"""Shared language-instruction helper for student-facing tutoring prompts
(teach, teach-back, practice, ask-a-doubt). Topic generation intentionally
stays out of scope — topics are generated once at upload time, not
per-request, so there's no per-interaction language choice to apply there.
"""

LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil (தமிழ்)",
}

DEFAULT_LANGUAGE = "en"


def language_instruction(language: str) -> str:
    name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES[DEFAULT_LANGUAGE])
    return (
        f"\n\nRespond entirely in {name}. Use natural, everyday {name} a "
        f"student would actually speak — not a stiff, overly literal "
        f"translation. Keep any textbook page references (like 'p.12') as "
        f"numerals."
    )
