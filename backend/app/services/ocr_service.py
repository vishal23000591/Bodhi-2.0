"""PaddleOCR wrapper. Imported lazily so the app runs without the (heavy,
optional) paddleocr/paddlepaddle dependencies installed — only the OCR
fallback path for scanned PDFs and photographed pages needs them.

Uses the PaddleOCR 3.x pipeline API (predict() returning OCRResult objects
with rec_texts/rec_scores) — the older 2.x ocr()/show_log/use_angle_cls
constructor args were removed upstream.
"""
from functools import lru_cache


class OcrUnavailableError(RuntimeError):
    """Raised when a scanned PDF needs OCR but paddleocr isn't installed."""


@lru_cache
def _get_engine():
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OcrUnavailableError(
            "This PDF has no selectable text and needs OCR, but paddleocr is not "
            "installed. Run: pip install -r requirements-ocr.txt"
        ) from exc
    return PaddleOCR(
        lang="en",
        use_textline_orientation=True,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    )


def ocr_image(image_path: str) -> str:
    engine = _get_engine()
    results = engine.predict(image_path)
    if not results:
        return ""
    texts = results[0].get("rec_texts") or []
    return " ".join(texts)
