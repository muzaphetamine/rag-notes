from pathlib import Path
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def generate_pdf(answer_file):
    with open(answer_file, "r", encoding="utf-8") as f:
        answers = json.load(f)

    pdf_folder = Path("output/pdfs")
    pdf_folder.mkdir(parents=True, exist_ok=True)

    output_file = pdf_folder / f"{answer_file.stem}.pdf"

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=20
    )

    question_style = ParagraphStyle(
        "QuestionStyle",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=10
    )

    answer_style = ParagraphStyle(
        "AnswerStyle",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=8
    )

    image_caption_style = ParagraphStyle(
        "ImageCaptionStyle",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        leading=12,
        spaceAfter=15
    )

    story = []

    # PDF title
    story.append(
        Paragraph(
            answer_file.stem,
            title_style
        )
    )

    for item in answers:

        label = item.get("label", "")
        question = item.get("question", "")
        answer = item.get("answer", "")
        images = item.get("images", [])

        # Question
        story.append(
            Paragraph(
                f"{label}. {question}",
                question_style
            )
        )

        # Answer
        # Convert newlines into HTML breaks for ReportLab
        answer_text = answer.replace("\n", "<br/>")

        story.append(
            Paragraph(
                answer_text,
                answer_style
            )
        )

        # Related images
        for image_data in images:

            image_path = Path(image_data["image_path"])

            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue

            try:
                img = Image(str(image_path))

                # Keep images inside page width
                max_width = 6.5 * inch
                max_height = 4.5 * inch

                width = img.imageWidth
                height = img.imageHeight

                scale = min(
                    max_width / width,
                    max_height / height,
                    1
                )

                img.drawWidth = width * scale
                img.drawHeight = height * scale

                story.append(Spacer(1, 8))
                story.append(img)

                caption = image_data.get("text", "")

                if caption:
                    story.append(
                        Paragraph(
                            caption,
                            image_caption_style
                        )
                    )

            except Exception as e:
                print(
                    f"Warning: Could not add image "
                    f"{image_path}: {e}"
                )

        story.append(Spacer(1, 15))

    doc.build(story)

    print(f"Generated → {output_file}")


def main():
    answer_folder = Path("output/answers")

    if not answer_folder.exists():
        print("No answers folder found.")
        return

    answer_files = list(answer_folder.glob("*.json"))

    if not answer_files:
        print("No answer JSON files found.")
        return

    for answer_file in answer_files:
        try:
            print(f"\nProcessing {answer_file.name}...")
            generate_pdf(answer_file)

        except Exception as e:
            print(
                f"✗ Failed on {answer_file.name}: {e}"
            )

    print("\nDone!")


if __name__ == "__main__":
    main()