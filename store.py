import chromadb
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer


def main():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="database/chroma")

    try:
        client.delete_collection("study_material")
        print("Deleted existing collection.")
    except Exception:
        print("No existing collection found.")
    collection = client.get_or_create_collection(
        name="study_material"
    )
    print("Collection ready.")


    documents=[]
    ids=[]
    metadatas=[]
    embeddings=None

    chunk_folder = Path("output/chunks")

    for chunk_file in chunk_folder.glob("*.json"):
        try:
            print(f"Processing {chunk_file.name}...")
            with open(chunk_file, 'r', encoding="utf-8") as f:
                chunks = json.load(f)
                chunk_num=1
                for chunk in chunks:
                    documents.append(chunk["text"])
                    ids.append(chunk["id"])
                    chunk_num+=1
                    curr_metadata={
                        "id": chunk["id"],
                        "source": chunk["source"],
                        #"page_start": min(chunk["pages"]),
                        #"page_end": max(chunk["pages"]),
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

    print("Done!")

    #results = collection.query(
    #    query_texts=["What is normalization?"],
    #    n_results=3
    #)
    #print(results)


if __name__ == "__main__":
    main()