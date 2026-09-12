from __future__ import annotations

from html import escape
from typing import Any, Dict
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem


class ReportService:
    """Render grounded pipeline results as a portable HTML report."""

    def render_html(self, result: Dict[str, Any]) -> str:
        sources = result.get("sources", [])
        source_markup = "".join(
            f"<li><strong>{escape(str(source.get('title', 'Unknown')))}</strong> "
            f"(chunk {escape(str(source.get('chunk_index', 'n/a')))})<br>"
            f"{escape(str(source.get('text_preview', '')))}</li>"
            for source in sources
        )
        verification = result.get("verification") or {}
        explanation_markup = "".join(f"<li>{escape(str(item))}</li>" for item in result.get("explanations", []))
        answer = escape(str(result.get("answer", ""))).replace("\n", "<br>")
        return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>TrustRAG report</title>
<style>body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.5;color:#172033}} h1{{color:#0f766e}} .meta{{background:#f1f5f9;padding:16px}} li{{margin:12px 0}}</style>
</head><body><h1>TrustRAG Evidence Report</h1>
<div class='meta'><strong>Query:</strong> {escape(str(result.get('query', '')))}<br>
<strong>Strategy:</strong> {escape(str(result.get('retrieval_strategy', 'unknown')))}<br>
<strong>Confidence:</strong> {float(result.get('confidence', 0)):.2%}<br>
<strong>Verification:</strong> {escape(str(verification.get('verification_status', 'UNKNOWN')))}</div>
<h2>Answer</h2><p>{answer}</p>
<h2>Sources</h2><ol>{source_markup or '<li>No sources returned.</li>'}</ol>
<h2>Explainability</h2><ul>{explanation_markup}</ul>
</body></html>"""

    def render_pdf(self, result: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch)
        styles = getSampleStyleSheet()
        story = [Paragraph("TrustRAG Evidence Report", styles["Title"]), Spacer(1, 12)]
        verification = result.get("verification") or {}
        metadata = [
            f"Query: {escape(str(result.get('query', '')))}",
            f"Retrieval strategy: {escape(str(result.get('retrieval_strategy', 'unknown')))}",
            f"Reranking: {escape(str(result.get('reranking_explanation', 'unknown')))}",
            f"Confidence: {float(result.get('confidence', 0)):.2%}",
            f"Verification: {verification.get('verification_status', 'UNKNOWN')}",
        ]
        story.append(ListFlowable([ListItem(Paragraph(item, styles["BodyText"])) for item in metadata], bulletType="bullet"))
        story.extend([Spacer(1, 12), Paragraph("Answer", styles["Heading2"]), Paragraph(escape(str(result.get("answer", ""))).replace("\n", "<br/>"), styles["BodyText"])])
        story.extend([Spacer(1, 12), Paragraph("Claims and verification", styles["Heading2"])])
        claims = verification.get("claims", [])
        story.append(ListFlowable([ListItem(Paragraph(f"{escape(str(claim.get('status')))}: {escape(str(claim.get('claim')))}", styles["BodyText"])) for claim in claims] or [ListItem(Paragraph("No structured claims returned.", styles["BodyText"]))], bulletType="bullet"))
        story.extend([Spacer(1, 12), Paragraph("Sources", styles["Heading2"])])
        sources = result.get("sources", [])
        story.append(ListFlowable([ListItem(Paragraph(f"{escape(str(source.get('title', 'Unknown')))} | chunk {escape(str(source.get('chunk_index', 'n/a')))}<br/>{escape(str(source.get('text_preview', '')))}", styles["BodyText"])) for source in sources] or [ListItem(Paragraph("No sources returned.", styles["BodyText"]))], bulletType="bullet"))
        document.build(story)
        return buffer.getvalue()
