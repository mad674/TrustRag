from __future__ import annotations

import re
from typing import Dict, List


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 160) -> List[Dict[str, object]]:
    """Create bounded overlapping chunks with stable structural metadata."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: List[Dict[str, object]] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(".", start, end)
            if boundary > start + max_chars // 2:
                end = boundary + 1
        value = normalized[start:end].strip()
        if value:
            chunks.append({"chunk_index": index, "text": value, "start_char": start, "end_char": end})
            index += 1
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
