from app.prompts.language import DEFAULT_LANGUAGE, language_instruction

ASK_SYSTEM_PROMPT = """You are Bodhi, a warm, encouraging tutor for school
students. Answer ONLY using the provided textbook excerpts below. If the
answer isn't in the excerpts, say clearly that it's not covered in this part
of the textbook — do not guess or use outside knowledge. Keep answers short,
simple, and matched to the textbook's own language and level."""

TEACH_SYSTEM_PROMPT = """You are Bodhi, a warm, encouraging tutor. Teach the
given topic to a school student using ONLY the textbook excerpts provided.
Explain clearly with a short example, 4-8 sentences, simple language, no
jargon beyond what's in the excerpts."""


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(no matching excerpts found)"
    return "\n\n".join(f"[p.{c['metadata'].get('page_number')}] {c['text']}" for c in chunks)


def build_ask_messages(
    question: str, chunks: list[dict], language: str = DEFAULT_LANGUAGE
) -> list[dict[str, str]]:
    context = format_context(chunks)
    return [
        {"role": "system", "content": ASK_SYSTEM_PROMPT + language_instruction(language)},
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"},
    ]


def build_teach_messages(
    topic_title: str, chunks: list[dict], language: str = DEFAULT_LANGUAGE
) -> list[dict[str, str]]:
    context = format_context(chunks)
    return [
        {"role": "system", "content": TEACH_SYSTEM_PROMPT + language_instruction(language)},
        {"role": "user", "content": f"TOPIC: {topic_title}\n\nCONTEXT:\n{context}"},
    ]
