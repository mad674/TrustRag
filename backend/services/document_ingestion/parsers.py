from __future__ import annotations

import io
import os
from typing import Dict, Any

from fastapi import HTTPException


def extract_text(filename: str, contents: bytes) -> Dict[str, Any]:
    extension = os.path.splitext(filename)[1].lower()
    if extension in {".txt", ".md", ".markdown"}:
        return {"text": contents.decode("utf-8", errors="ignore"), "page_count": None}
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            pages = PdfReader(io.BytesIO(contents)).pages
            return {"text": "\n".join(page.extract_text() or "" for page in pages), "page_count": len(pages)}
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}") from exc
    if extension == ".docx":
        try:
            from docx import Document
            document = Document(io.BytesIO(contents))
            return {"text": "\n".join(paragraph.text for paragraph in document.paragraphs), "page_count": None}
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not parse DOCX: {exc}") from exc
    raise HTTPException(status_code=400, detail="Supported files: PDF, DOCX, TXT, Markdown")
