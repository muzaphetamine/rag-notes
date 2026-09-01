from pathlib import Path
from docling_core.types.doc import DoclingDocument
from docling.chunking import HybridChunker
import json


def report(message, progress_callback=None):
    print(message)
    if progress_callback:
        progress_callback(message)


def group_table_chunks(raw_chunks):
    groups=[]
    table_groups_by_ref={}
    for ch in raw_chunks:
        doc_items = ch.meta.doc_items
        table_ref = None
        for item in doc_items:
            if item.label == "table":
                table_ref = item.self_ref
                break

        if table_ref is None:
            groups.append([ch])
        else:
            if table_ref not in table_groups_by_ref:
                new_group = []
                table_groups_by_ref[table_ref] = new_group
                groups.append(new_group)
            table_groups_by_ref[table_ref].append(ch)
    return groups


def merge_group_text(group, chunker, heading):
    pieces=[]
    for c in group:
        text = chunker.serialize(chunk=c)
        if heading and text.startswith(heading):
            text = text[len(heading):].lstrip("\n")
        pieces.append(text)
    body = "\n".join(pieces)
    return f"{heading}\n{body}" if heading else body


def chunk_document(json_path: Path, progress_callback=None):
    doc = DoclingDocument.load_from_json(json_path)
    file_name = json_path.stem
    chunker = HybridChunker(
        tokenizer="sentence-transformers/all-MiniLM-L6-v2",
        max_tokens=150,
    )

    chunks = []
    for i, group in enumerate( group_table_chunks(chunker.chunk(doc)), start=1):
        heading = (
            group[0].meta.headings[0]
            if group[0].meta.headings
            else ""
        )
        text =merge_group_text(group,chunker, heading)
        chunks.append({
            "id": f"{file_name}_{i}",
            "source": file_name,
            "text": text,
            "heading": heading,
            "type": "text"
        })

    image_chunks = []
    image_chunk_id = 1
    for image_index, picture in enumerate(doc.pictures, start=1):
        caption = picture.caption_text(doc).strip()
        if not caption:
            continue
        image_path = (
            Path("output/images")
            / file_name
            / f"image_{image_index}.png"
        )
        image_chunks.append({
            "id": f"{file_name}_img_{image_chunk_id}",
            "source": file_name,
            "text": caption,
            "heading": caption,
            "type": "image",
            "image_path": str(image_path)
        })
        image_chunk_id += 1

    text_out_path =(Path("output/chunks") / f"{file_name}_chunks.json")
    text_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open( text_out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4,ensure_ascii=False)

    image_out_path =(Path("output/image_chunks") / f"{file_name}_image_chunks.json")
    image_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(image_out_path, "w", encoding="utf-8") as f:
        json.dump(image_chunks, f,indent=4, ensure_ascii=False)

    report(
        f"{file_name}: "
        f"{len(chunks)} text/table chunks, "
        f"{len(image_chunks)} image chunks",
        progress_callback
    )
    report(f"-> {text_out_path}", progress_callback)
    report(f"-> {image_out_path}", progress_callback)


def process_chunking(progress_callback=None):
    json_folder = Path("output/docjson")
    for json_file in json_folder.glob("*.json"):
        try:
            chunk_document(json_file, progress_callback)
        except Exception as e:
            report(f"Failed on {json_file.name}: {e}", progress_callback)
    report("Chunking done!", progress_callback)

def main():
    process_chunking()


if __name__ == "__main__":
    main()