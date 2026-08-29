from pathlib import Path
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Preformatted,
)
from xml.sax.saxutils import escape


def markdown_inline(text):
    text =escape(text)
    #Inline code
    text =re.sub(
        r"`([^`]+)`",
        r'<font name="Courier">\1</font>',
        text
    )
    #Bold
    text =re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text
    )
    #Italic
    text =re.sub(
        r"(?<!\*)\*([^*]+?)\*(?!\*)",
        r"<i>\1</i>",
        text
    )
    return text


def markdown_to_flowables(text, styles):
    flowables=[]
    lines=text.splitlines()
    i= 0
    while i < len(lines):
        line =lines[i].rstrip()
        #Blank line
        if not line.strip():
            flowables.append(Spacer(1, 6))
            i+= 1
            continue
        #Fenced code block
        if line.strip().startswith("```"):
            code_lines=[]
            i+= 1
            while i<len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i+= 1
            #Skip closing ```
            if i < len(lines):
                i+= 1
            code_text ="\n".join(code_lines)
            flowables.append(
                Preformatted(
                    code_text,
                    styles["CodeBlock"]
                )
            )
            flowables.append(Spacer(1, 8))
            continue
        #Markdown H1
        if re.match(r"^#\s+", line):
            heading = re.sub(r"^#\s+", "", line)
            flowables.append(
                Paragraph(
                    markdown_inline(heading),
                    styles["MarkdownH1"]
                )
            )
            i+=1
            continue
        #Markdown H2
        if re.match(r"^##\s+", line):
            heading=re.sub(r"^##\s+", "", line)
            flowables.append(
                Paragraph(
                    markdown_inline(heading),
                    styles["MarkdownH2"]
                )
            )
            i += 1
            continue
        #Markdown H3
        if re.match(r"^###\s+", line):
            heading = re.sub(r"^###\s+", "", line)
            flowables.append(
                Paragraph(
                    markdown_inline(heading),
                    styles["MarkdownH3"]
                )
            )
            i+=1
            continue
        #Bullet list
        bullet_match =re.match(r"^\s*[-*]\s+(.+)", line)
        if bullet_match:
            content = bullet_match.group(1)
            flowables.append(
                Paragraph(
                    "• " + markdown_inline(content),
                    styles["Bullet"]
                )
            )
            i+= 1
            continue
        #Numbered list
        numbered_match =re.match(
            r"^\s*(\d+)[.)]\s+(.+)",
            line
        )
        if numbered_match:
            number =numbered_match.group(1)
            content =numbered_match.group(2)
            flowables.append(
                Paragraph(
                    f"<b>{number}.</b> {markdown_inline(content)}",
                    styles["Numbered"]
                )
            )
            i += 1
            continue
        #Normal paragraph
        flowables.append(
            Paragraph(
                markdown_inline(line),
                styles["Answer"]
            )
        )
        i+= 1
    return flowables


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
        bottomMargin=50,
    )
    styles =getSampleStyleSheet()
    #Main PDF title
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    #Question
    question_style = ParagraphStyle(
        "QuestionStyle",
        parent=styles["BodyText"],
        fontSize=14,
        leading=17,
        spaceBefore=14,
        spaceAfter=10,
        fontName="Helvetica-Bold",
    )
    #Markdown headings
    markdown_h1= ParagraphStyle(
        "MarkdownH1",
        parent=styles["BodyText"],
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=6,
    )
    markdown_h2= ParagraphStyle(
        "MarkdownH2",
        parent=styles["BodyText"],
        fontSize=12,
        leading=15,
        spaceBefore=7,
        spaceAfter=5,
    )
    markdown_h3= ParagraphStyle(
        "MarkdownH3",
        parent=styles["BodyText"],
        fontSize=11,
        leading=14,
        spaceBefore=6,
        spaceAfter=4,
    )
    #Normal answer text
    answer_style = ParagraphStyle(
        "Answer",
        parent=styles["BodyText"],
        leading=15,
        spaceAfter=5,
    )
    #Bullet
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=answer_style,
        leftIndent=15,
        firstLineIndent=0,
        spaceAfter=4,
    )
    #Numbered list
    numbered_style= ParagraphStyle(
        "Numbered",
        parent=answer_style,
        leftIndent=5,
        firstLineIndent=0,
        spaceAfter=5,
    )
    #Code/ASCII diagrams
    code_style =ParagraphStyle(
        "CodeBlock",
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        leftIndent=15,
        spaceBefore=5,
        spaceAfter=10,
    )
    image_caption_style =ParagraphStyle(
        "ImageCaptionStyle",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        leading=12,
        spaceAfter=15,
    )
    styles_dict = {
        "MarkdownH1": markdown_h1,
        "MarkdownH2": markdown_h2,
        "MarkdownH3": markdown_h3,
        "Answer": answer_style,
        "Bullet": bullet_style,
        "Numbered": numbered_style,
        "CodeBlock": code_style,
    }
    story = []
    #PDF title
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
        #Question
        story.append(
            Paragraph(
                f"{escape(label)}. {markdown_inline(question)}",
                question_style
            )
        )
        #Markdown-aware answer
        story.extend(
            markdown_to_flowables(
                answer,
                styles_dict
            )
        )
        #Related images
        for image_data in images:
            image_path = Path(image_data["image_path"])
            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue
            try:
                img = Image(str(image_path))
                max_width = 6.5 * inch
                max_height = 4.5 * inch
                width =img.imageWidth
                height =img.imageHeight
                scale =min(
                    max_width / width,
                    max_height / height,
                    1
                )
                img.drawWidth =width * scale
                img.drawHeight =height * scale
                story.append(Spacer(1, 8))
                story.append(img)
                caption = image_data.get(
                    "text",
                    ""
                )
                if caption:
                    story.append(
                        Paragraph(
                            markdown_inline(caption),
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
            print(f"✗ Failed on {answer_file.name}: {e}")
    print("\nDone!")


if __name__ == "__main__":
    main()