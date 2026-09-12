from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResearchDocumentProfile:
    """Optional metadata profile for papers and technical reports."""

    title: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
