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


def report(message, progress_callback=None):
    print(message)
    if progress_callback:
        progress_callback(message)


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


def convert_folder(input_dir: Path, output_dir: Path, progress_callback=None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files =[
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        report(f"No supported files found in {input_dir}", progress_callback)
        return

    report(f"Found {len(files)} file(s) to convert.\n", progress_callback)
    converter = create_converter()
    succeeded = []
    failed = []
    for i, file_path in enumerate(files, start=1):
        out_path = output_dir / f"{file_path.stem}.json"
        if out_path.exists():
            print(f"[{i}/{len(files)}] ")
            report(f"Skipping {file_path.name} (already converted)", progress_callback)
            succeeded.append(file_path.name)
            continue

        report(f"[{i}/{len(files)}] Converting {file_path.name} ...", progress_callback)
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
            print(f"saved {out_path.name}")
            succeeded.append(file_path.name)
        except Exception as e:
            report(f"FAILED: {file_path.name} -> {e}", progress_callback)
            failed.append((file_path.name, str(e)))

    print("\n--- Summary ---")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed:    {len(failed)}")
    if failed:
        print("\nFailed files:")
        for name, err in failed:
            print(f"  - {name}: {err}")


def extract_question_banks(input_dir: Path, output_dir: Path, progress_callback=None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        report(f"No question-bank files found in {input_dir}", progress_callback)
        return

    print(f"\nFound {len(files)} question-bank file(s).\n")
    converter = create_converter()
    for i, file_path in enumerate(files, start=1):
        out_path = output_dir / f"{file_path.stem}.json"
        if out_path.exists():
            print(f"[{i}/{len(files)}] ")
            report(f"Skipping {file_path.name} (already extracted)", progress_callback)
            continue

        print(f"[{i}/{len(files)}] ")
        report(f"Extracting questions from {file_path.name} ...", progress_callback)
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
            report(f"saved {out_path.name} ({len(questions)} questions)", progress_callback)
        except Exception as e:
            report(f"FAILED: {file_path.name} -> {e}", progress_callback)


def process_extraction(
    source_dir=Path("input/sources"),
    source_output=Path("output/docjson"),
    question_dir=Path("input/questions"),
    question_output=Path("output/questions"),
    progress_callback=None
):
    if not source_dir.exists():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")
    if not question_dir.exists():
        raise FileNotFoundError(f"Question folder not found: {question_dir}")
    convert_folder(source_dir, source_output, progress_callback)
    extract_question_banks(question_dir, question_output, progress_callback)
    report("\nDone!", progress_callback)


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

    process_extraction(source_dir,source_output,question_dir,question_output)


if __name__ == "__main__":
    main()