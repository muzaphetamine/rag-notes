import chromadb
import json
from sentence_transformers import SentenceTransformer
from pathlib import Path
from rank_bm25 import BM25Okapi
import re

model =SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
client =chromadb.PersistentClient(path="database/chroma")

try:
    collection =client.get_collection("study_material")
except Exception:
    print("No indexed knowledge base found. Run store.py first.")
    exit()

try:
    image_collection= client.get_collection("study_images")
except Exception:
    image_collection = None
    print("No image base found.")


def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.split()


docs=[]
bm25_metadata = []
chunk_folder= Path("output/chunks")
for chunk_file in chunk_folder.glob("*.json"):
    try:
        print(f"Processing {chunk_file.name}...")
        with open(chunk_file, 'r', encoding="utf-8") as f:
            chunks =json.load(f)
            for chunk in chunks:
                docs.append(chunk["text"])
                bm25_metadata.append({
                    "id": chunk["id"],
                    "source": chunk["source"],
                    "heading": chunk["heading"]
                })
    except Exception as e:
        print(f"✗ Failed on {chunk_file.name}: {e}")
print(f"Loaded {len(docs)} chunks.")

tokenized_corpus= [preprocess(doc) for doc in docs]
bm25 = BM25Okapi(tokenized_corpus)
print("bm25 index done.")


def retrieve(question, k=3,n=3):
    query_tokens=preprocess(question)
    scores= bm25.get_scores(query_tokens)
    top_indices = scores.argsort()[-k:][::-1]
    bm25_results=[]
    for i in top_indices:
        bm25_results.append({
            "id": bm25_metadata[i]['id'],
            "source": bm25_metadata[i]['source'],
            "heading": bm25_metadata[i]["heading"],
            "text": docs[i],
            "retrieval_score": scores[i],
            "retriever": "bm25"
        })

    question_embedding = model.encode(question)
    raw_results = collection.query(
        query_embeddings= [question_embedding.tolist()],
        n_results= n,
        include=["documents", "metadatas", "distances"]
    )
    chroma_results=[]
    for i in range(len(raw_results["ids"][0])):
        chroma_results.append({
            "id": raw_results["metadatas"][0][i]['id'],
            "source": raw_results["metadatas"][0][i]['source'],
            "heading": raw_results["metadatas"][0][i]["heading"],
            "text": raw_results["documents"][0][i],
            "retrieval_score": raw_results["distances"][0][i],
            "retriever": "chroma"
        })   
    return bm25_results, chroma_results


def fuse(bm25_results, chroma_results):
    rrf_scores={}
    rrf_results={}
    rrf_k=60

    def add_rrf(retrieved_res):
        for rank, result in enumerate(retrieved_res, start=1):
            if result["id"] not in rrf_scores:
                rrf_scores[result["id"]]=1/(rrf_k + rank)
                rrf_results[result["id"]]=result
            else:
                rrf_scores[result["id"]]+=1/(rrf_k + rank)

    add_rrf(bm25_results)
    add_rrf(chroma_results)
    sorted_rrf = sorted(rrf_scores, key=lambda id: rrf_scores[id], reverse=True)
    results=[]
    for id in sorted_rrf:
        result = rrf_results[id]
        result["rrf_score"] = rrf_scores[id]
        results.append(result)
    return results


def image_retrieve(question, n=3):
    if image_collection is None or image_collection.count() == 0:
        return []
    question_embedding = model.encode(question)
    raw_results = image_collection.query(
        query_embeddings= [question_embedding.tolist()],
        n_results= n,
        include=["documents", "metadatas", "distances"]
    )
    image_results=[]
    for i in range(len(raw_results["ids"][0])):
        image_results.append({
            "id": raw_results["metadatas"][0][i]['id'],
            "source": raw_results["metadatas"][0][i]['source'],
            "heading": raw_results["metadatas"][0][i]["heading"],
            "image_path": raw_results["metadatas"][0][i]["image_path"],
            "text": raw_results["documents"][0][i],
            "retrieval_score": raw_results["distances"][0][i],
            "retriever": "image_chroma"
        })
    return image_results


def fuse_multiple(result_sets):
    rrf_scores={}
    rrf_results={}
    rrf_k=60
    for results in result_sets:
        for rank, result in enumerate(results, start=1):
            result_id = result["id"]
            if result_id not in rrf_scores:
                rrf_scores[result_id] = 1 / (rrf_k + rank)
                rrf_results[result_id] = result
            else:
                rrf_scores[result_id] += 1 / (rrf_k + rank)
    sorted_ids =sorted(
        rrf_scores,
        key=lambda id: rrf_scores[id],
        reverse=True
    )
    final_results=[]
    for result_id in sorted_ids:
        result = rrf_results[result_id]
        result["rrf_score"] = rrf_scores[result_id]
        final_results.append(result)
    return final_results
