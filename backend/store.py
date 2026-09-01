import chromadb
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

def store_text(model, collection):
    documents=[]
    ids=[]
    metadatas=[]
    chunk_folder = Path("output/chunks")
    for chunk_file in chunk_folder.glob("*.json"):
        try:
            print(f"Processing {chunk_file.name}...")
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
            print(f"✗ Failed on {chunk_file.name}: {e}")

    if documents:
        print("Generating embeddings...")
        embeddings = model.encode(documents)
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        print(f"Stored {len(documents)} chunks in Chroma.")
    else:
        print("No documents found to store.")


def store_images(model, image_collection):
    documents=[]
    ids=[]
    metadatas=[]
    chunk_folder = Path("output/image_chunks")
    for chunk_file in chunk_folder.glob("*.json"):
        try:
            print(f"Processing {chunk_file.name}...")
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
            print(f"✗ Failed on {chunk_file.name}: {e}")

    if documents:
        print("Generating embeddings...")
        embeddings = model.encode(documents)
        image_collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
            embeddings=embeddings.tolist()
        )
        print(f"Stored {len(documents)} chunks in Chroma.")
    else:
        print("No documents found to store.")


def main():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="database/chroma")

    try:
        client.delete_collection("study_material")
        client.delete_collection("study_images")
        print("Deleted existing collection.")
    except Exception:
        print("No existing collections found.")
    collection = client.get_or_create_collection( name="study_material" )
    image_collection = client.get_or_create_collection( name="study_images" )
    print("Collections ready.")

    store_text(model, collection)
    store_images(model, image_collection)
    print("Done!")


if __name__ == "__main__":
    main()