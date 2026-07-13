"""
Microsoft MarkItDown wrapper for BusinessPilot AI.

Converts uploaded documents to clean Markdown for LLM consumption.
Supports PDF, DOCX, PPTX, XLSX, images, and plain text via the
`markitdown` package (pip install markitdown). Falls back to manual
handling for text-based formats when the package is unavailable.
"""

import os
import tempfile


def _try_markitdown(file_path: str) -> str | None:
    """Try converting via microsoft/markitdown. Returns None if unavailable."""
    try:
        from markitdown import MarkItDown

        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        text = result.text_content
        if text and text.strip():
            return text.strip()
    except Exception:
        pass
    return None


def convert_to_markdown(file_content: bytes, filename: str) -> str:
    """Convert uploaded file bytes to clean Markdown text.

    Uses `markitdown` for binary formats (PDF, DOCX, etc.) with a
    manual text fallback for .txt / .csv / .md files.
    Returns plain Markdown string — no JSON wrapping, no raw API responses.
    """
    ext = os.path.splitext(filename)[1].lower()

    # --- Plain text formats: write to disk and try markitdown, else raw ---
    if ext in (".txt", ".md", ".csv", ".json", ".xml"):
        text = file_content.decode("utf-8", errors="replace")
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        try:
            result = _try_markitdown(tmp_path)
            if result:
                return result
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        return text.strip() or "(empty file)"

    # --- Binary formats: write to temp file, try markitdown ---
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    try:
        result = _try_markitdown(tmp_path)
        if result:
            return result
        return (
            f"[{filename}] This file format ({ext}) requires the `markitdown` package. "
            f"Install it with: pip install markitdown\n\n"
            f"File size: {len(file_content):,} bytes"
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
