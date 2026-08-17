"""Shared language-instruction helper for student-facing tutoring prompts
(teach, teach-back, practice, ask-a-doubt). Topic generation intentionally
stays out of scope — topics are generated once at upload time, not
per-request, so there's no per-interaction language choice to apply there.
"""

DEFAULT_LANGUAGE = "en"

_PAGE_REFERENCE_NOTE = "Keep any textbook page references (like 'p.12') as numerals."

_INSTRUCTIONS = {
    "en": f"Respond entirely in English. {_PAGE_REFERENCE_NOTE}",
    "ta": (
        "Respond entirely in Tamil (தமிழ்), written in Tamil script. Use "
        "natural, everyday Tamil a student would actually speak — not a "
        f"stiff, overly literal translation. {_PAGE_REFERENCE_NOTE}"
    ),
    "tanglish": (
        "Respond entirely in Tanglish: spoken Tamil written using the "
        "English (Roman) alphabet, the way Tamil speakers commonly type "
        "Tamil in everyday texting — for example, 'Ithu eppadi work aagum "
        "nu paakalam' rather than Tamil script or formal English. The "
        "words and grammar should be Tamil, just spelled out phonetically "
        "in English letters — do NOT switch to Tamil script, and do NOT "
        "just write formal English. Naturally mixing in a few common "
        f"English words, the way real Tanglish speech does, is fine. {_PAGE_REFERENCE_NOTE}"
    ),
}


def language_instruction(language: str) -> str:
    instruction = _INSTRUCTIONS.get(language, _INSTRUCTIONS[DEFAULT_LANGUAGE])
    return f"\n\n{instruction}"
