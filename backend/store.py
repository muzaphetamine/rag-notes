import chromadb
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer


def report(message, progress_callback=None):
    print(message)
    if progress_callback:
        progress_callback(message)


def store_text(model, collection, progress_callback=None):
    documents=[]
    ids=[]
    metadatas=[]
    chunk_folder = Path("output/chunks")
    for chunk_file in chunk_folder.glob("*.json"):
        try:
            report(f"Processing {chunk_file.name}...", progress_callback)
            with open(chunk_file, 'r', encoding="utf-8") as f:
                chunks = json.load(f)
                for chunk in chunks:
                    documents.append(chunk["text"])
                    ids.append(chunk["id"])
                    curr_metadata={
                        "id": chunk["id"],
                        "source": chunk["source"],
                        "heading": chunk["heading"]
                    }
                    metadatas.append(curr_metadata)
        except Exception as e:
            report(f"Failed on {chunk_file.name}: {e}", progress_callback)

    if documents:
        report("Generating embeddings...", progress_callback)
        embeddings = model.encode(documents)
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        report(f"Stored {len(documents)} chunks in Chroma.", progress_callback)
    else:
        report("No documents found to store.", progress_callback)


def store_images(model, image_collection, progress_callback=None):
    documents=[]
    ids=[]
    metadatas=[]
    chunk_folder = Path("output/image_chunks")
    for chunk_file in chunk_folder.glob("*.json"):
        try:
            report(f"Processing {chunk_file.name}...", progress_callback)
            with open(chunk_file, 'r', encoding="utf-8") as f:
                chunks = json.load(f)
                for chunk in chunks:
                    documents.append(chunk["text"])
                    ids.append(chunk["id"])
                    curr_metadata={
                        "id": chunk["id"],
                        "source": chunk["source"],
                        "heading": chunk["heading"],
                        "image_path": chunk["image_path"]
                    }
                    metadatas.append(curr_metadata)
        except Exception as e:
            report(f"Failed on {chunk_file.name}: {e}", progress_callback)

    if documents:
        report("Generating embeddings...", progress_callback)
        embeddings = model.encode(documents)
        image_collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        report(f"Stored {len(documents)} chunks in Chroma.", progress_callback)
    else:
        report("No documents found to store.", progress_callback)


def process_store(progress_callback=None):
    report("Loading embedding model...", progress_callback)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="database/chroma")

    try:
        client.delete_collection("study_material")
        client.delete_collection("study_images")
        report("Deleted existing collection.", progress_callback)
    except Exception:
        report("No existing collections found.", progress_callback)
    collection = client.get_or_create_collection( name="study_material" )
    image_collection = client.get_or_create_collection( name="study_images" )
    report("Collections ready.", progress_callback)

    store_text(model, collection, progress_callback)
    store_images(model, image_collection, progress_callback)
    report("Done!", progress_callback)


def main():
    process_store()


if __name__ == "__main__":
    main()