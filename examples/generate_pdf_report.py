#!/usr/bin/env python3
"""Example: Generate a multi-page PDF report using Strategy 2 (Data + Driver).

This is the exact pattern used to build the X Profile Analysis report.
It demonstrates how to handle large static content (report text, tables)
without hitting write_file truncation limits.
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# PART 1: Data serialization (run this in a small execute_code call)
# ---------------------------------------------------------------------------

def create_report_data():
    """Build the report content structure. Can be arbitrarily large."""
    return {
        "meta": {
            "title": "X Profile Analysis Report",
            "author": "Hermes Agent",
            "subject": "@example_user",
            "date": "April 2026"
        },
        "sections": [
            {
                "num": "01",
                "title": "PERSONALITY MAP",
                "subsections": [
                    {
                        "title": "Core Identity Archetypes",
                        "archetypes": [
                            ("The Tech Operator", "8/10",
                             "Speaks freely about engineering, product trade-offs, and infrastructure."),
                            ("The Evangelist", "7/10",
                             "MSME credit mission present but less front-and-center than on LinkedIn."),
                            ("The Contrarian", "7/10",
                             "Debunks AI hype, mocks API wrappers. Gets more engagement than mission posts."),
                        ]
                    }
                ]
            },
            {
                "num": "02",
                "title": "PROFILE AUDIT",
                "checks": [
                    ("Bio present", "PASS", "Clear and differentiated."),
                    ("Website link", "FAIL", "No linktree or direct URL. Conversion leak."),
                    ("Pin tweet", "PARTIAL", "Dated 2024 Polkadot repost, off-brand for fintech."),
                ],
                "score": "4/7 checks passed"
            }
        ],
        "kpi": [
            ["Metric", "Current", "30-Day", "90-Day"],
            ["Followers", "215", "300", "500"],
            ["Originals/Week", "2", "3", "4"],
            ["Threads/Month", "0", "2", "4"],
        ]
    }


def save_data(data, path="/tmp/report_data.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    print(f"Data saved to {path} ({os.path.getsize(path)} bytes)")


# ---------------------------------------------------------------------------
# PART 2: Compact driver (run this in a second execute_code call)
# ---------------------------------------------------------------------------

def generate_pdf(data_path, output_path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.colors import HexColor

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=0.7*inch, leftMargin=0.7*inch,
                            topMargin=0.8*inch, bottomMargin=0.8*inch)
    styles = getSampleStyleSheet()

    def MS(name, parent, **k):
        return ParagraphStyle(name, parent=parent, **k)

    h1 = MS('H1', styles['Heading1'], fontName='Helvetica-Bold', fontSize=22,
            leading=28, textColor=HexColor('#1a1a1a'), spaceAfter=12, spaceBefore=18)
    h2 = MS('H2', styles['Heading2'], fontName='Helvetica-Bold', fontSize=14,
            leading=18, textColor=HexColor('#333333'), spaceAfter=8, spaceBefore=12)
    body = MS('Body', styles['Normal'], fontName='Helvetica', fontSize=10,
              leading=14, textColor=HexColor('#333333'), spaceAfter=8)
    item = MS('Item', styles['Normal'], fontName='Helvetica-Bold', fontSize=10,
              leading=13, textColor=HexColor('#1a1a1a'), spaceBefore=7, spaceAfter=1)

    def b(t): return f"<b>{t}</b>"
    sec = lambda num, title: Paragraph(f"<font color='#999999'>{num}</font>  <b>{title}</b>", h1)

    story = []
    meta = data["meta"]

    # Cover
    story.append(Spacer(1, 1.2*inch))
    story.append(Paragraph(meta["title"], MS('BT', styles['Normal'], fontName='Helvetica-Bold',
                                            fontSize=36, leading=42, textColor=HexColor('#1a1a1a'))))
    story.append(Paragraph(f"Prepared: {meta['date']}<br/>By: {meta['author']}", body))
    story.append(PageBreak())

    # Sections
    for section in data["sections"]:
        story.append(sec(section["num"], section["title"]))
        for sub in section.get("subsections", []):
            if sub.get("title"):
                story.append(Paragraph(sub["title"], h2))
            if "archetypes" in sub:
                for name, score, desc in sub["archetypes"]:
                    story.append(Paragraph(f"{b(name)}  <font color='#666666'>{score}</font>", item))
                    story.append(Paragraph(desc, body))
            if "checks" in sub:
                for check, status, detail in sub["checks"]:
                    color = "#2d8a3e" if status == "PASS" else ("#b35900" if status == "PARTIAL" else "#cc3333")
                    story.append(Paragraph(
                        f"<font color='{color}'><b>[{status}]</b></font>  {b(check)}<br/>{detail}",
                        body))
                story.append(Paragraph(f"Score: {b(section.get('score', 'N/A'))}", body))
        story.append(PageBreak())

    # KPI table
    kpi = data.get("kpi", [])
    if kpi:
        story.append(Paragraph("KPIs", h2))
        rows = [[Paragraph(b(c), body) for c in kpi[0]]]
        for row in kpi[1:]:
            rows.append([Paragraph(c, body) for c in row])
        t = Table(rows, colWidths=[2*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)

    doc.build(story)
    size = os.path.getsize(output_path)
    print(f"PDF generated: {output_path} ({size} bytes)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-data", action="store_true", help="Only save data JSON")
    parser.add_argument("--data-path", default="/tmp/report_data.json")
    parser.add_argument("--output", default="/tmp/example_report.pdf")
    args = parser.parse_args()

    if args.save_data:
        save_data(create_report_data(), args.data_path)
    else:
        if not os.path.exists(args.data_path):
            save_data(create_report_data(), args.data_path)
        generate_pdf(args.data_path, args.output)
