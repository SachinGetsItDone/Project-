"""Resume parsing: extract plain text from an uploaded resume.

Supports PDF (via ``pypdf``) and plain-text/markdown uploads. Returns the
extracted text, which becomes ``interviews.resume_text`` and feeds the
interviewer's candidate context.
"""

import io


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data)
    # Treat everything else as UTF-8 text (txt, md, etc.).
    try:
        return data.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        parts = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(parts).strip()
    except Exception as e:
        print(f"Resume PDF parse failed: {e}")
        return ""
