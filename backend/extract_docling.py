import os
import argparse
import json
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from llm import extract_questions

os.environ["TORCHINDUCTOR_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"
SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx"}


def create_converter():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images=True
    pipeline_options.images_scale=2.0

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )


def convert_folder(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files =[
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        print(f"No supported files found in {input_dir}")
        return

    print(f"Found {len(files)} file(s) to convert.\n")
    converter = create_converter()
    succeeded = []
    failed = []
    for i, file_path in enumerate(files, start=1):
        out_path = output_dir / f"{file_path.stem}.json"
        if out_path.exists():
            print(
                f"[{i}/{len(files)}] "
                f"Skipping {file_path.name} (already converted)"
            )
            succeeded.append(file_path.name)
            continue

        print(f"[{i}/{len(files)}] Converting {file_path.name} ...")
        try:
            result = converter.convert(str(file_path))
            doc = result.document
            image_dir = Path("output/images") / file_path.stem
            image_dir.mkdir(parents=True, exist_ok=True)
            for j, picture in enumerate(doc.pictures, start=1):
                image = picture.get_image(doc)
                if image is not None:
                    image_path = image_dir / f"image_{j}.png"
                    image.save(image_path)
                    print(f"    -> saved image {image_path}")

            doc.save_as_json(out_path)
            print(f"    -> saved {out_path.name}")
            succeeded.append(file_path.name)
        except Exception as e:
            print(f"    !! FAILED: {file_path.name} -> {e}")
            failed.append((file_path.name, str(e)))

    print("\n--- Summary ---")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed:    {len(failed)}")
    if failed:
        print("\nFailed files:")
        for name, err in failed:
            print(f"  - {name}: {err}")


def extract_question_banks(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        print(f"No question-bank files found in {input_dir}")
        return

    print(f"\nFound {len(files)} question-bank file(s).\n")
    converter = create_converter()
    for i, file_path in enumerate(files, start=1):
        out_path = output_dir / f"{file_path.stem}.json"
        if out_path.exists():
            print(
                f"[{i}/{len(files)}] "
                f"Skipping {file_path.name} (already extracted)"
            )
            continue

        print(
            f"[{i}/{len(files)}] "
            f"Extracting questions from {file_path.name} ..."
        )
        try:
            result = converter.convert(str(file_path))
            doc = result.document
            text = doc.export_to_markdown()
            questions = extract_questions(text)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(
                    questions,
                    f,
                    indent=4,
                    ensure_ascii=False
                )
            print(
                f"    -> saved {out_path.name} "
                f"({len(questions)} questions)"
            )
        except Exception as e:
            print(f"    !! FAILED: {file_path.name} -> {e}")


def main():
    parser = argparse.ArgumentParser(description="Extract study material and question banks using Docling")
    parser.add_argument("--input",type=str,default="input/sources",help="Folder containing study material")
    parser.add_argument("--output",type=str,default="output/docjson",help="Folder to write study-material Docling JSON")
    parser.add_argument("--questions",type=str,default="input/questions",help="Folder containing question banks")

    args = parser.parse_args()
    source_dir = Path(args.input)
    source_output = Path(args.output)
    question_dir = Path(args.questions)
    question_output = Path("output/questions")

    if not source_dir.exists():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")
    if not question_dir.exists():
        raise FileNotFoundError(f"Question folder not found: {question_dir}")

    convert_folder(source_dir, source_output)
    extract_question_banks(question_dir, question_output)
    print("\nDone!")


if __name__ == "__main__":
    main()