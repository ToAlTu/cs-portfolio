from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

def parse_resume_content(content):
    result = {"summary": "", "skills": "", "projects": [], "experience": []}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "SUMMARY":
            i += 1
            summary_lines = []
            while i < len(lines) and not lines[i].strip().startswith(("SKILLS", "PROJECT:", "EXPERIENCE:")):
                summary_lines.append(lines[i].strip())
                i += 1
            result["summary"] = " ".join(summary_lines).strip()
        elif line.startswith("SKILLS"):
            i += 1
            result["skills"] = lines[i].strip() if i < len(lines) else ""
            i += 1
        elif line.startswith("PROJECT:"):
            project = {"header": line.replace("PROJECT:", "").strip(), "technologies": "", "bullets": []}
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(("PROJECT:", "EXPERIENCE:", "SUMMARY", "SKILLS")):
                l = lines[i].strip()
                if l.startswith("TECHNOLOGIES:"):
                    project["technologies"] = l.replace("TECHNOLOGIES:", "").strip()
                elif l.startswith("- "):
                    project["bullets"].append(l[2:])
                i += 1
            result["projects"].append(project)
        elif line.startswith("EXPERIENCE:"):
            exp = {"header": line.replace("EXPERIENCE:", "").strip(), "bullets": []}
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(("PROJECT:", "EXPERIENCE:", "SUMMARY", "SKILLS")):
                l = lines[i].strip()
                if l.startswith("- "):
                    exp["bullets"].append(l[2:])
                i += 1
            result["experience"].append(exp)
        else:
            i += 1
    return result

def generate_pdf(resume_content, full_name, contact_info, filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle("Name", fontSize=20, fontName="Helvetica-Bold", spaceAfter=8, alignment=1)
    contact_style = ParagraphStyle("Contact", fontSize=9, fontName="Helvetica", spaceAfter=4, textColor=colors.HexColor("#444444"), alignment=1)
    section_header_style = ParagraphStyle("SectionHeader", fontSize=11, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("Body", fontSize=8.5, fontName="Helvetica", spaceAfter=2, leading=12)
    project_title_style = ParagraphStyle("ProjectTitle", fontSize=9.5, fontName="Helvetica-Bold", spaceAfter=1, keepWithNext=1)
    sub_style = ParagraphStyle("Sub", fontSize=8.5, fontName="Helvetica-Oblique", spaceAfter=2, textColor=colors.HexColor("#555555"), keepWithNext=1)
    bullet_style = ParagraphStyle("Bullet", fontSize=8.5, fontName="Helvetica", spaceAfter=2, leading=12, leftIndent=12, firstLineIndent=-8)
    section_header_style = ParagraphStyle("SectionHeader", fontSize=10.5, fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3, keepWithNext=1, textColor=colors.HexColor("#000000"))

    data = parse_resume_content(resume_content)
    story = []

    # Header
    header_text = f"{full_name}<br/><font size='9' color='#444444'>{contact_info}</font>"
    header_style = ParagraphStyle("Header", fontSize=20, fontName="Helvetica-Bold", alignment=1, spaceAfter=8, leading=28)
    story.append(Paragraph(header_text, header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    # Summary
    if data["summary"]:
        story.append(Paragraph("SUMMARY", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(data["summary"], body_style))

    # Skills
    if data["skills"]:
        story.append(Spacer(1, 6))
        story.append(Paragraph("SKILLS", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(data["skills"], body_style))

    # Projects
    if data["projects"]:
        story.append(Spacer(1, 6))
        story.append(Paragraph("PROJECTS", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        story.append(Spacer(1, 4))
        for project in data["projects"]:
            story.append(Paragraph(project["header"], project_title_style))
            if project["technologies"]:
                story.append(Paragraph(f"Technologies: {project['technologies']}", sub_style))
            for bullet in project["bullets"]:
                story.append(Paragraph(f"• {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    # Experience
    if data["experience"]:
        story.append(Spacer(1, 6))
        story.append(Paragraph("EXPERIENCE", section_header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        story.append(Spacer(1, 4))
        for exp in data["experience"]:
            story.append(Paragraph(exp["header"], project_title_style))
            for bullet in exp["bullets"]:
                story.append(Paragraph(f"• {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    print(f"PDF saved as {filename}")