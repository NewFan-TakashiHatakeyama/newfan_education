"""Render the persisted report snapshot; never mark missing files completed."""
import csv
from io import BytesIO, StringIO
from xml.sax.saxutils import escape


def render_report(report, report_format):
    if report_format == "csv":
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["reportId", "title", "summary", "version", "createdBy", "generatedAt"])
        def cell(value):
            value = str(value)
            return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
        writer.writerow([cell(report[k]) for k in ("id", "title", "summary", "version", "createdBy", "generatedAt")])
        return output.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8"
    if report_format != "pdf":
        raise ValueError("Unsupported report format")
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    style = ParagraphStyle("Japanese", fontName="HeiseiKakuGo-W5", fontSize=10, leading=16, wordWrap="CJK")
    stream = BytesIO()
    paragraphs = [report["title"], report["summary"], f"{report['id']} / v{report['version']} / {report['generatedAt']}"]
    story = []
    for text in paragraphs:
        story.extend([Paragraph(escape(text).replace("\n", "<br/>"), style), Spacer(1, 16)])
    SimpleDocTemplate(stream).build(story)
    content = stream.getvalue()
    if not content.startswith(b"%PDF-"):
        raise RuntimeError("PDF generation failed")
    return content, "application/pdf"
