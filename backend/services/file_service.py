"""File generation service — HTML-to-PDF and DOCX generation."""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from backend.config import settings

logger = logging.getLogger(__name__)

jinja_env = Environment(
    loader=FileSystemLoader(settings.TEMPLATE_DIR),
    autoescape=True,
)


class FileService:

    def render_template(self, template_name: str, context: dict) -> str:
        """Render an HTML template with context data."""
        try:
            template = jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return f"<html><body><p>Template error: {e}</p></body></html>"

    def generate_pdf(self, html_content: str, filename: Optional[str] = None) -> str:
        """Generate PDF from HTML content. Returns file path."""
        if not filename:
            filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(settings.GENERATED_DIR, filename)

        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(filepath)
            return filepath
        except ImportError:
            logger.warning("weasyprint not installed. Saving as HTML instead.")
            html_path = filepath.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return html_path
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            # Fallback: save HTML
            html_path = filepath.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return html_path

    def generate_docx(self, resume_data: dict, filename: Optional[str] = None) -> str:
        """Generate DOCX from resume data. Returns file path."""
        if not filename:
            filename = f"resume_{uuid.uuid4().hex[:8]}.docx"
        filepath = os.path.join(settings.GENERATED_DIR, filename)

        try:
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # Style setup
            style = doc.styles['Normal']
            style.font.name = 'Calibri'
            style.font.size = Pt(11)

            # Name
            name = resume_data.get("full_name", "Your Name")
            heading = doc.add_heading(name, level=0)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Contact
            contact = resume_data.get("contact", {})
            contact_parts = [v for v in contact.values() if v]
            if contact_parts:
                p = doc.add_paragraph(" | ".join(contact_parts))
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Summary
            if resume_data.get("summary"):
                doc.add_heading("Professional Summary", level=1)
                doc.add_paragraph(resume_data["summary"])

            # Experience
            experience = resume_data.get("experience", [])
            if experience:
                doc.add_heading("Experience", level=1)
                for exp in experience:
                    p = doc.add_paragraph()
                    run = p.add_run(f"{exp.get('title', '')} — {exp.get('company', '')}")
                    run.bold = True
                    p.add_run(f"\n{exp.get('location', '')} | {exp.get('dates', '')}")
                    for bullet in exp.get("bullets", []):
                        doc.add_paragraph(bullet, style='List Bullet')

            # Education
            education = resume_data.get("education", [])
            if education:
                doc.add_heading("Education", level=1)
                for edu in education:
                    p = doc.add_paragraph()
                    run = p.add_run(f"{edu.get('degree', '')} — {edu.get('school', '')}")
                    run.bold = True
                    p.add_run(f"\n{edu.get('dates', '')}")

            # Skills
            skills = resume_data.get("skills", {})
            if skills:
                doc.add_heading("Skills", level=1)
                if isinstance(skills, dict):
                    for category, skill_list in skills.items():
                        if skill_list:
                            doc.add_paragraph(f"{category.replace('_', ' ').title()}: {', '.join(skill_list)}")
                elif isinstance(skills, list):
                    doc.add_paragraph(", ".join(skills))

            # Projects
            projects = resume_data.get("projects", [])
            if projects:
                doc.add_heading("Projects", level=1)
                for proj in projects:
                    p = doc.add_paragraph()
                    run = p.add_run(proj.get("name", ""))
                    run.bold = True
                    if proj.get("description"):
                        doc.add_paragraph(proj["description"])

            doc.save(filepath)
            return filepath

        except ImportError:
            logger.error("python-docx not installed")
            return ""
        except Exception as e:
            logger.error(f"DOCX generation error: {e}")
            return ""

    def generate_txt(self, resume_data: dict, filename: Optional[str] = None) -> str:
        """Generate plain text resume."""
        if not filename:
            filename = f"resume_{uuid.uuid4().hex[:8]}.txt"
        filepath = os.path.join(settings.GENERATED_DIR, filename)

        lines = []
        lines.append(resume_data.get("full_name", "Your Name").upper())
        contact = resume_data.get("contact", {})
        lines.append(" | ".join(v for v in contact.values() if v))
        lines.append("=" * 60)

        if resume_data.get("summary"):
            lines.append("\nPROFESSIONAL SUMMARY")
            lines.append("-" * 40)
            lines.append(resume_data["summary"])

        for exp in resume_data.get("experience", []):
            lines.append(f"\n{exp.get('title', '')} — {exp.get('company', '')}")
            lines.append(f"{exp.get('location', '')} | {exp.get('dates', '')}")
            for bullet in exp.get("bullets", []):
                lines.append(f"  • {bullet}")

        if resume_data.get("education"):
            lines.append("\nEDUCATION")
            lines.append("-" * 40)
            for edu in resume_data.get("education", []):
                lines.append(f"{edu.get('degree', '')} — {edu.get('school', '')} ({edu.get('dates', '')})")

        skills = resume_data.get("skills", {})
        if skills:
            lines.append("\nSKILLS")
            lines.append("-" * 40)
            if isinstance(skills, dict):
                for cat, slist in skills.items():
                    if slist:
                        lines.append(f"{cat.replace('_', ' ').title()}: {', '.join(slist)}")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath


file_service = FileService()
