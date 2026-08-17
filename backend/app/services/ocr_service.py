"""PaddleOCR wrapper. Imported lazily so the app runs without the (heavy,
optional) paddleocr/paddlepaddle dependencies installed — only the OCR
fallback path for scanned PDFs needs them.
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
    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


def ocr_image(image_path: str) -> str:
    engine = _get_engine()
    result = engine.ocr(image_path, cls=True)
    if not result or not result[0]:
        return ""
    return " ".join(line[1][0] for line in result[0])
