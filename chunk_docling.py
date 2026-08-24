from pathlib import Path
from docling_core.types.doc import DoclingDocument
from docling.chunking import HybridChunker
import json

def group_table_chunks(raw_chunks):
    """
    Takes the list of raw chunk objects from chunker.chunk(doc) (before serialization).
    Returns a new list of raw-chunk-like groups: table chunks belonging to the same
    TableItem are merged into one group; everything else passes through as single-item groups.

    Each returned group is a list of original chunks -- caller decides how to
    merge .text / .meta when building the final output dict.
    """
    groups = []
    table_groups_by_ref = {}  # self_ref of TableItem -> group (list of chunks)

    for ch in raw_chunks:
        # doc_items tells us which structural element(s) this chunk's text came from
        doc_items = ch.meta.doc_items

        # find if this chunk is table-derived, and get a stable id for that table
        table_ref = None
        for item in doc_items:
            if item.label == "table":          # DocItemLabel.TABLE
                table_ref = item.self_ref        # e.g. "#/tables/3" -- stable per table
                break

        if table_ref is None:
            # prose / non-table chunk -> passes through untouched
            groups.append([ch])
        else:
            # table chunk -> accumulate into the group for this specific table
            if table_ref not in table_groups_by_ref:
                new_group = []
                table_groups_by_ref[table_ref] = new_group
                groups.append(new_group)   # preserve original ordering by first appearance
            table_groups_by_ref[table_ref].append(ch)

    return groups


def merge_group_text(group, chunker, heading):
    """
    group: list of chunk objects belonging to the same table (or a single-item
           list for prose). Returns the final merged text with the heading
           appearing only once.
    """
    pieces = []
    for c in group:
        text = chunker.serialize(chunk=c)
        # each fragment's serialized text starts with the heading line(s) --
        # strip that off every fragment, we'll add it back once at the end
        if heading and text.startswith(heading):
            text = text[len(heading):].lstrip("\n")
        pieces.append(text)

    body = "\n".join(pieces)
    return f"{heading}\n{body}" if heading else body


def chunk_document(json_path: Path):
    doc = DoclingDocument.load_from_json(json_path)
    file_name = json_path.stem

    chunker = HybridChunker(
        tokenizer="sentence-transformers/all-MiniLM-L6-v2",
        max_tokens=150,
    )

    chunks = []
    for i, group in enumerate(group_table_chunks(chunker.chunk(doc)), start=1):
        heading = group[0].meta.headings[0] if group[0].meta.headings else ""
        text = merge_group_text(group, chunker, heading)
        chunks.append({
            "id": f"{file_name}_{i}",
            "source": file_name,
            "text": text,
            "heading": heading,
        })

    
    out_path = Path("output/chunks") / f"{file_name}_chunks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4, ensure_ascii=False)

    print(f"{file_name}: {len(chunks)} chunks -> {out_path}")


def main():
    json_folder = Path("output/docjson")
    for json_file in json_folder.glob("*.json"):
        try:
            chunk_document(json_file)
        except Exception as e:
            print(f"✗ Failed on {json_file.name}: {e}")
    print("Done!")


if __name__ == "__main__":
    main()