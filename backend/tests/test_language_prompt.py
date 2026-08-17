from app.prompts.language import language_instruction


def test_english_instruction_mentions_english():
    instruction = language_instruction("en")
    assert "English" in instruction
    assert "Tamil" not in instruction


def test_tamil_instruction_specifies_tamil_script():
    instruction = language_instruction("ta")
    assert "Tamil" in instruction
    assert "Tamil script" in instruction


def test_tanglish_instruction_specifies_roman_alphabet_not_script():
    instruction = language_instruction("tanglish")
    assert "Tanglish" in instruction
    assert "Roman" in instruction
    assert "do NOT switch to Tamil script" in instruction


def test_unknown_language_falls_back_to_english():
    assert language_instruction("fr") == language_instruction("en")


def test_each_language_produces_a_distinct_instruction():
    instructions = {language_instruction(lang) for lang in ("en", "ta", "tanglish")}
    assert len(instructions) == 3
