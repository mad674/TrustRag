from __future__ import annotations

import os
from typing import Dict, Optional


def extract_metadata(filename: str, contents: bytes, page_count: Optional[int] = None) -> Dict[str, object]:
    return {
        "filename": os.path.basename(filename),
        "file_type": os.path.splitext(filename)[1].lstrip(".").lower(),
        "file_size": len(contents),
        "page_count": page_count,
    }
