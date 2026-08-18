"""PyMuPDF-first extraction with a PaddleOCR fallback for scanned/image PDFs.

PyMuPDF is always tried first on every upload (fast, no ML inference, and
it's also what rasterizes pages for OCR). PaddleOCR is only invoked when the
average extractable text per page falls below MIN_CHARS_PER_PAGE.
"""
import os

import pymupdf as fitz

from app.services.ocr_service import ocr_image

DEFAULT_MIN_CHARS_PER_PAGE = 30


def extract_text(
    pdf_path: str,
    *,
    min_chars_per_page: int = DEFAULT_MIN_CHARS_PER_PAGE,
    tmp_dir: str = "/tmp",
) -> tuple[list[dict], str]:
    """Returns (pages, extraction_mode) where extraction_mode is
    'copy_paste' or 'ocr', and pages is [{"page_number": int, "text": str}]."""
    doc = fitz.open(pdf_path)
    try:
        pages = []
        is_copy_paste = True
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if len(text) < min_chars_per_page:
                is_copy_paste = False
            pages.append({"page_number": i + 1, "text": text})

        if is_copy_paste:
            return pages, "copy_paste"

        ocr_pages = []
        os.makedirs(tmp_dir, exist_ok=True)
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=200)
            img_path = os.path.join(tmp_dir, f"{doc_id}_page_{i + 1}.png")
            pix.save(img_path)
            try:
                text = ocr_image(img_path)
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)
            ocr_pages.append({"page_number": i + 1, "text": text})
        return ocr_pages, "ocr"
    finally:
        doc.close()


def get_page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    try:
        return doc.page_count
    finally:
        doc.close()


def images_to_pdf(image_bytes_list: list[bytes]) -> bytes:
    """Combines one or more page photos (JPG/PNG/WEBP/...) into a single
    multi-page PDF, in the given order. The result has no text layer, so
    extract_text's existing copy-paste check naturally routes it through
    the PaddleOCR fallback — no separate image-extraction path needed."""
    merged = fitz.open()
    try:
        for image_bytes in image_bytes_list:
            img_doc = fitz.open(stream=image_bytes, filetype="image")
            try:
                single_page_pdf = fitz.open("pdf", img_doc.convert_to_pdf())
                try:
                    merged.insert_pdf(single_page_pdf)
                finally:
                    single_page_pdf.close()
            finally:
                img_doc.close()
        return merged.tobytes()
    finally:
        merged.close()
