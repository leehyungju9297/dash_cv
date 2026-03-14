import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESUME_DIR = ROOT / 'resume'
SOURCE_PATH = RESUME_DIR / 'resume.json'
MARKDOWN_PATH = RESUME_DIR / 'Hyungju_Lee_Resume.md'
PDF_PATH = ROOT / 'assets' / 'Hyungju_Lee_Resume.pdf'
DOCX_PATH = ROOT / 'assets' / 'Hyungju_Lee_Resume.docx'
DOCS_PDF_PATH = ROOT / 'docs' / 'assets' / 'Hyungju_Lee_Resume.pdf'
DOCS_DOCX_PATH = ROOT / 'docs' / 'assets' / 'Hyungju_Lee_Resume.docx'


def load_resume():
    return json.loads(SOURCE_PATH.read_text())


def escape(text):
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def build_markdown(resume):
    basics = resume['basics']
    lines = [
        f"# {basics['name']}",
        '',
        f"{basics['location']} | {basics['phone']} | {basics['email']}",
        f"LinkedIn: {basics['linkedin']} | Website: {basics['website']}",
        '',
        resume['headline'],
        '',
        '## Professional Summary',
    ]

    for item in resume['summary']:
        lines.append(f"- {item}")

    lines.extend(['', '## Skills'])
    for group in resume['skills']:
        lines.append(f"- **{group['label']}:** {', '.join(group['items'])}")

    lines.extend(['', '## Experience'])
    for job in resume['experience']:
        lines.append(
            f"### {job['company']} | {job['role']} | {job['location']}"
        )
        lines.append(job['period'])
        for bullet in job['bullets']:
            lines.append(f"- {bullet}")
        lines.append('')

    lines.append('## Education')
    for edu in resume['education']:
        entry = f"- **{edu['degree']}**, {edu['school']} ({edu['period']})"
        if 'note' in edu:
            entry += f" | {edu['note']}"
        lines.append(entry)

    MARKDOWN_PATH.write_text('\n'.join(lines).rstrip() + '\n')


def build_pdf(resume):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        'Name',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1f3550'),
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=9.6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#555555'),
        spaceAfter=2,
    )
    headline_style = ParagraphStyle(
        'Headline',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.1,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#24384f'),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.3,
        leading=10.5,
        textColor=colors.HexColor('#24384f'),
        spaceBefore=5,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10.0,
        textColor=colors.black,
        spaceAfter=2,
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=8,
        spaceAfter=1,
    )
    entry_header_style = ParagraphStyle(
        'EntryHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=10.2,
        textColor=colors.HexColor('#222222'),
        spaceAfter=0,
    )
    period_style = ParagraphStyle(
        'Period',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=9.0,
        textColor=colors.HexColor('#555555'),
        spaceAfter=1,
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.46 * inch,
        rightMargin=0.46 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    basics = resume['basics']
    story = [
        Paragraph(escape(basics['name']), name_style),
        Paragraph(
            escape(f"{basics['location']} | {basics['phone']} | {basics['email']}"),
            contact_style,
        ),
        Paragraph(
            escape(f"LinkedIn: {basics['linkedin']} | Website: {basics['website']}"),
            contact_style,
        ),
        Spacer(1, 2),
        Paragraph(escape(resume['headline']), headline_style),
    ]

    def add_section(title):
        story.append(Paragraph(escape(title.upper()), section_style))
        story.append(
            HRFlowable(
                width='100%',
                color=colors.HexColor('#8ca0b3'),
                thickness=0.7,
                spaceBefore=0,
                spaceAfter=3,
            )
        )

    add_section('Professional Summary')
    for item in resume['summary']:
        story.append(Paragraph(escape(item), body_style))

    add_section('Skills')
    for group in resume['skills']:
        text = f"<b>{escape(group['label'])}:</b> {escape(', '.join(group['items']))}"
        story.append(Paragraph(text, body_style))

    add_section('Experience')
    for job in resume['experience']:
        header = ' | '.join([job['company'], job['role'], job['location']])
        story.append(Paragraph(escape(header), entry_header_style))
        story.append(Paragraph(escape(job['period']), period_style))
        for bullet in job['bullets']:
            story.append(Paragraph(f"- {escape(bullet)}", bullet_style))

    add_section('Education')
    for edu in resume['education']:
        line = f"{edu['degree']}, {edu['school']} ({edu['period']})"
        if 'note' in edu:
            line += f" | {edu['note']}"
        story.append(Paragraph(f"- {escape(line)}", bullet_style))

    doc.build(story)


def build_docx():
    pandoc = shutil.which('pandoc')
    if not pandoc:
        raise RuntimeError('pandoc is required to build the DOCX resume.')

    subprocess.run(
        [pandoc, str(MARKDOWN_PATH), '-o', str(DOCX_PATH)],
        check=True,
    )


def sync_docs():
    shutil.copy2(PDF_PATH, DOCS_PDF_PATH)
    shutil.copy2(DOCX_PATH, DOCS_DOCX_PATH)


def main():
    resume = load_resume()
    build_markdown(resume)
    build_pdf(resume)
    build_docx()
    sync_docs()
    print(f'Built {PDF_PATH}')
    print(f'Built {DOCX_PATH}')


if __name__ == '__main__':
    try:
        main()
    except ModuleNotFoundError as exc:
        if exc.name == 'reportlab':
            print(
                'Missing dependency: reportlab. Install it with '
                '`python3 -m pip install -r resume/requirements.txt`.',
                file=sys.stderr,
            )
            raise SystemExit(1)
        raise
