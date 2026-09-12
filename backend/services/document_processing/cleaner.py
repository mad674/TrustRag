from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries."""
    paragraphs = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in paragraphs if line)
