"""Static, reviewer-readable PDF rendering for an authentication report."""
from __future__ import annotations

from pathlib import Path
from html import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

from .models import AuthenticationReport


def render_pdf(report: AuthenticationReport, path: str | Path) -> None:
    document = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="AI Image Authentication Report")
    styles = getSampleStyleSheet()
    story = [Paragraph("AI Image Authentication Report", styles["Title"]), Spacer(1, 8 * mm), Paragraph("Human-review record only. This report is not a judicial conclusion or proof of origin.", styles["BodyText"]), Spacer(1, 5 * mm)]
    rows = [["Field", "Value"], ["Report ID", report.analysis_id], ["Input SHA-256", report.input_sha256], ["Analysis time (UTC)", report.analysis_time_utc], ["Authenticity assessment", report.assessment.authenticity_status], ["Confidence", report.assessment.confidence_level], ["Risk level", report.risk_level], ["Output SHA-256", report.output_sha256]]
    table = Table(rows, colWidths=(48 * mm, 118 * mm))
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9aa9b7")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.extend([table, Spacer(1, 6 * mm), Paragraph("Evidence summary", styles["Heading2"])])
    story.extend(Paragraph(item, styles["BodyText"]) for item in report.assessment.evidence_summary)
    story.extend([Spacer(1, 4 * mm), Paragraph("Evidence list", styles["Heading2"])])
    for observation in report.evidence["provenance"] + report.evidence["image"]:
        story.append(Paragraph(f"{escape(str(observation['id']))} - {escape(str(observation['type']))} - source: {escape(str(observation['source']))} - method: {escape(str(observation['method_version']))}<br/>{escape(str(observation['limitation']))}", styles["BodyText"]))
    for item in report.evidence.get("providers", []):
        provenance = item["evidence_provenance"]
        story.append(Paragraph(f"Provider evidence: {escape(item['provider_id'])}@{escape(item['provider_version'])} - source: {escape(provenance['source_type'])} - evidence: {escape(provenance['evidence_id'])}<br/>{escape('; '.join(item['limitations']))}", styles["BodyText"]))
    for item in report.evidence.get("model_evidence", []):
        observation = item["observation"]
        story.append(Paragraph(f"Model evidence: {escape(observation['model']['model_id'])}@{escape(observation['model']['version'])}; scope: {escape(observation['scope_status'])}; score: {escape(str(observation['score']))}; calibration: {escape(observation['validation']['calibration_id'])}.", styles["BodyText"]))
    if report.evidence["model"] is None:
        story.append(Paragraph("Model evidence: not used.", styles["BodyText"]))
    else:
        story.append(Paragraph(f"Model evidence: {report.evidence['model']['identifier']}@{report.evidence['model']['version']}; admission: {report.evidence['model']['admission_id']}.", styles["BodyText"]))
    story.extend([Spacer(1, 4 * mm), Paragraph("Limitations", styles["Heading2"])])
    story.extend(Paragraph(item, styles["BodyText"]) for item in report.limitations)
    methods = ", ".join(f"{item['name']}@{item['version']}" for item in report.evidence["methods"])
    story.extend([Spacer(1, 4 * mm), Paragraph("Audit trail", styles["Heading2"]), Paragraph(f"Submitter: {report.audit_trail['submitter_id']}<br/>Tool version: {report.audit_trail['tool_version']}<br/>Methods: {methods}<br/>Evidence completeness: {report.evidence['evidence_completeness']}<br/>Explainability score: {report.evidence['explainability_score']}", styles["BodyText"])])
    document.build(story)
