import pymupdf

from app.documents.document_service import extract_text, get_page_count, images_to_pdf


def _png_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=18)
    pix = page.get_pixmap(dpi=150)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


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


def test_images_to_pdf_creates_one_page_per_image():
    pdf_bytes = images_to_pdf([_png_bytes("Page one content"), _png_bytes("Page two content")])

    doc = pymupdf.open("pdf", pdf_bytes)
    try:
        assert doc.page_count == 2
    finally:
        doc.close()


def test_images_to_pdf_single_image():
    pdf_bytes = images_to_pdf([_png_bytes("Just one page")])

    doc = pymupdf.open("pdf", pdf_bytes)
    try:
        assert doc.page_count == 1
    finally:
        doc.close()


def test_images_converted_to_pdf_have_no_text_layer_and_route_to_ocr(monkeypatch, tmp_path):
    """A photographed page becomes an image-only PDF page — extract_text
    should treat it exactly like a scanned PDF and use the OCR fallback."""
    pdf_bytes = images_to_pdf([_png_bytes("Photosynthesis happens in chloroplasts.")])
    pdf_path = tmp_path / "from_images.pdf"
    pdf_path.write_bytes(pdf_bytes)

    calls = []

    def fake_ocr_image(image_path):
        calls.append(image_path)
        return "Photosynthesis happens in chloroplasts."

    monkeypatch.setattr("app.documents.document_service.ocr_image", fake_ocr_image)

    pages, mode = extract_text(str(pdf_path), min_chars_per_page=30, tmp_dir=str(tmp_path / "ocr_tmp"))

    assert mode == "ocr"
    assert len(pages) == 1
    assert len(calls) == 1
    assert pages[0]["text"] == "Photosynthesis happens in chloroplasts."
