TOPIC_SYSTEM_PROMPT = """You are an expert curriculum designer. Given raw textbook
content (with page markers like [p.12]), extract 8-15 distinct teachable
concepts/topics, in the order they appear.

Return STRICT JSON only, in this exact shape:
{"topics": [{"title": "...", "page_range": [start, end], "description": "..."}]}

Rules:
- title: short, student-facing (3-6 words)
- page_range: the [start, end] page numbers (from the [p.N] markers) this topic is grounded in
- description: one sentence, plain language
- Cover the whole document; do not invent topics not present in the text."""

# Guards against oversized prompts. A real page-batched map-reduce for very
# long books is future work (see architecture doc section 4).
MAX_INPUT_CHARS = 60_000


def build_topic_messages(text: str) -> list[dict[str, str]]:
    truncated = text[:MAX_INPUT_CHARS]
    return [
        {"role": "system", "content": TOPIC_SYSTEM_PROMPT},
        {"role": "user", "content": truncated},
    ]
