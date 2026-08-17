from app.documents.document_service import extract_text, get_page_count


def test_copy_paste_pdf_uses_pymupdf_text(sample_pdf_path):
    pages, mode = extract_text(sample_pdf_path, min_chars_per_page=30)

    assert mode == "copy_paste"
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Photosynthesis" in pages[0]["text"]
    assert "Page 2" in pages[1]["text"]


def test_scanned_pdf_falls_back_to_ocr(blank_pdf_path, monkeypatch, tmp_path):
    calls = []

    def fake_ocr_image(image_path):
        calls.append(image_path)
        return "ocr text for a page"

    monkeypatch.setattr("app.documents.document_service.ocr_image", fake_ocr_image)

    pages, mode = extract_text(
        blank_pdf_path, min_chars_per_page=30, tmp_dir=str(tmp_path / "ocr_tmp")
    )

    assert mode == "ocr"
    assert len(pages) == 2
    assert len(calls) == 2
    assert all(p["text"] == "ocr text for a page" for p in pages)


def test_get_page_count(sample_pdf_path):
    assert get_page_count(sample_pdf_path) == 2
