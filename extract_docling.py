import os
os.environ["TORCHINDUCTOR_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

import argparse
from pathlib import Path
from docling.document_converter import DocumentConverter

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx"}


def convert_folder(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"No supported files (.pdf, .pptx, .docx) found in {input_dir}")
        return

    print(f"Found {len(files)} file(s) to convert.\n")

    converter = DocumentConverter()

    succeeded = []
    failed = []

    for i, file_path in enumerate(files, start=1):
        out_path = output_dir / f"{file_path.stem}.json"

        # Skip if already converted (so re-running doesn't redo everything)
        if out_path.exists():
            print(f"[{i}/{len(files)}] Skipping {file_path.name} (already converted)")
            succeeded.append(file_path.name)
            continue

        print(f"[{i}/{len(files)}] Converting {file_path.name} ...")
        try:
            result = converter.convert(str(file_path))
            # Save the full DoclingDocument structure (headings, tables, text, provenance)
            # instead of flattening to markdown -- this is what HybridChunker needs later.
            result.document.save_as_json(out_path)

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


def main():
    parser = argparse.ArgumentParser(description="Batch convert docs to Docling JSON")
    parser.add_argument("--input", type=str, default="input", help="Folder containing source files")
    parser.add_argument("--output", type=str, default="output/docjson", help="Folder to write .json files to")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    convert_folder(input_dir, output_dir)


if __name__ == "__main__":
    main()