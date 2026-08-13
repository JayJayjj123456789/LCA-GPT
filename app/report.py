import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


def _build_styles():
    """Create custom styles matching the dark theme."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontSize=24,
        textColor=colors.HexColor("#58a6ff"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        fontSize=12,
        textColor=colors.HexColor("#8b949e"),
        spaceAfter=20,
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=16,
        textColor=colors.HexColor("#58a6ff"),
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyDark",
        fontSize=10,
        textColor=colors.HexColor("#30363d"),
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        name="FooterSmall",
        fontSize=8,
        textColor=colors.HexColor("#8b949e"),
        fontName="Helvetica",
    ))
    return styles


def generate_pdf_report(data: dict) -> bytes:
    """Generate an ISO 14067-style carbon footprint PDF report.

    Args:
        data: Analysis dict from AI (project_info, materials, energy, transport, etc.)

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = _build_styles()
    story = []

    # --- COVER / HEADER ---
    story.append(Paragraph("CARBON FOOTPRINT REPORT", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Project: {data.get('project_info', {}).get('name', 'N/A')} | "
        f"Supplier: {data.get('project_info', {}).get('supplier', 'N/A')}",
        styles["ReportSubtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#30363d")))
    story.append(Spacer(1, 6 * mm))

    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("📋 EXECUTIVE SUMMARY", styles["SectionHeader"]))
    summary = data.get("summary", "No summary available.")
    story.append(Paragraph(summary, styles["BodyDark"]))
    story.append(Spacer(1, 4 * mm))

    # Key metrics table
    total_co2 = float(data.get("total_estimated_co2") or 0)
    score = data.get("optimization_score", 0)
    metrics_data = [
        ["Metric", "Value"],
        ["Total Carbon Footprint", f"{total_co2:,.2f} kgCO₂e"],
        ["Optimization Score", f"{score}/100"],
        ["Materials Tracked", str(len(data.get("materials", [])))],
        ["Energy Entries", str(len(data.get("energy", [])))],
        ["Transport Entries", str(len(data.get("transport", [])))],
    ]
    metrics_table = Table(metrics_data, colWidths=[80 * mm, 80 * mm])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#161b22")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#58a6ff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#30363d")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 6 * mm))

    # --- MATERIALS TABLE ---
    if data.get("materials"):
        story.append(Paragraph("📦 MATERIALS", styles["SectionHeader"]))
        mat_header = ["Material", "Amount", "Unit", "EF (kgCO₂e)", "Subtotal"]
        mat_rows = [mat_header]
        for m in data["materials"]:
            amount = float(m.get("amount") or 0)
            ef = float(m.get("emission_factor") or 0)
            subtotal = amount * ef
            mat_rows.append([
                m["name"],
                f"{amount:,.2f}",
                m.get("unit", ""),
                f"{ef:,.4f}",
                f"{subtotal:,.2f}",
            ])
        mat_table = Table(mat_rows, colWidths=[35 * mm, 25 * mm, 20 * mm, 30 * mm, 30 * mm])
        mat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d29922")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#30363d")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff8dc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(mat_table)
        story.append(Spacer(1, 4 * mm))

    # --- ENERGY TABLE ---
    if data.get("energy"):
        story.append(Paragraph("⚡ ENERGY", styles["SectionHeader"]))
        en_header = ["Type", "Usage", "Unit", "EF (kgCO₂e)", "Subtotal"]
        en_rows = [en_header]
        for e in data["energy"]:
            usage = float(e.get("usage") or 0)
            ef = float(e.get("emission_factor") or 0)
            subtotal = usage * ef
            en_rows.append([
                e["type"],
                f"{usage:,.2f}",
                e.get("unit", "kWh"),
                f"{ef:,.4f}",
                f"{subtotal:,.2f}",
            ])
        en_table = Table(en_rows, colWidths=[35 * mm, 25 * mm, 20 * mm, 30 * mm, 30 * mm])
        en_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f85149")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#30363d")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff0f0")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(en_table)
        story.append(Spacer(1, 4 * mm))

    # --- TRANSPORT TABLE ---
    if data.get("transport"):
        story.append(Paragraph("🚚 TRANSPORT", styles["SectionHeader"]))
        tr_header = ["Method", "Distance", "Unit", "EF (kgCO₂e)", "Subtotal"]
        tr_rows = [tr_header]
        for t in data["transport"]:
            distance = float(t.get("distance") or 0)
            ef = float(t.get("emission_factor") or 0)
            subtotal = distance * ef
            tr_rows.append([
                t["method"],
                f"{distance:,.2f}",
                t.get("unit", "km"),
                f"{ef:,.4f}",
                f"{subtotal:,.2f}",
            ])
        tr_table = Table(tr_rows, colWidths=[35 * mm, 25 * mm, 20 * mm, 30 * mm, 30 * mm])
        tr_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a371f7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#30363d")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f0ff")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tr_table)
        story.append(Spacer(1, 6 * mm))

    # --- RECOMMENDATIONS ---
    if data.get("recommendations"):
        story.append(Paragraph("💡 RECOMMENDATIONS", styles["SectionHeader"]))
        for i, rec in enumerate(data["recommendations"], 1):
            story.append(Paragraph(f"{i}. {rec}", styles["BodyDark"]))
            story.append(Spacer(1, 2 * mm))
        story.append(Spacer(1, 4 * mm))

    # --- METHODOLOGY ---
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#30363d")))
    story.append(Paragraph("📐 METHODOLOGY", styles["SectionHeader"]))
    story.append(Paragraph(
        "This report follows the ISO 14067 standard for carbon footprint of products "
        "and IPCC 2019 guidelines for greenhouse gas inventory. "
        "Emission factors are sourced from TGO (Thailand), Ecoinvent 3.8, and GLEC Framework v3.",
        styles["BodyDark"],
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "Formula: CO₂e = Σ (Activity Data × Emission Factor)",
        styles["BodyDark"],
    ))

    # --- FOOTER ---
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d0d7de")))
    story.append(Paragraph(
        f"Generated by LCA-GPT Enterprise | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Page <page>",
        styles["FooterSmall"],
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
