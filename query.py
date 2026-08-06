import chromadb
import json
from sentence_transformers import SentenceTransformer
from pathlib import Path
from rank_bm25 import BM25Okapi

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="database/chroma")

try:
    collection = client.get_collection("study_material")
except Exception:
    print("No indexed knowledge base found. Run store.py first.")
    exit()


#getting chunks from json for bm25
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
                    "page_start": min(chunk["pages"]),
                    "page_end": max(chunk["pages"])
                })
    except Exception as e:
        print(f"✗ Failed on {chunk_file.name}: {e}")
print(f"Loaded {len(docs)} chunks.")

tokenized_corpus= [doc.lower().split() for doc in docs]
#print(tokenized_corpus[0])
bm25 = BM25Okapi(tokenized_corpus)
print("bm25 index done.")




question = input("Enter your question: ")

#print("----------BM25 RETRIVAL------------------------")
query_tokens=question.lower().split()
scores= bm25.get_scores(query_tokens)
k=3
top_indices = scores.argsort()[-k:][::-1]
#for i in top_indices:
#    print(scores[i])
#    print(bm25_metadata[i])
#    print(docs[i])
bm25_results=[]
for i in top_indices:
    bm25_results.append({
        "id": bm25_metadata[i]['id'],
        "source": bm25_metadata[i]['source'],
        "page_start": bm25_metadata[i]['page_start'],
        "page_end": bm25_metadata[i]['page_end'],
        "text": docs[i],
        "retrieval_score": scores[i],
        "retriever": "bm25"
    })


#print("\n\n\n----------CHROMADB RETRIVAL------------------------")
question_embedding = model.encode(question)
raw_results = collection.query(
    query_embeddings= [question_embedding.tolist()],
    n_results= 3,
    include=["documents", "metadatas", "distances"]
)
#ids=results["ids"][0]
#documents=results["documents"][0]
#metadatas=results["metadatas"][0]
#distances= results["distances"][0]
#for i in range(len(ids)):
#    print("\n------------------------------------------------")
#    print(f"Rank: {i+1} Distance: {distances[i]} Source: {metadatas[i]['source']}")
#    print(f"Pages: {metadatas[i]['page_start']}-{metadatas[i]['page_end']}")
#    print("--------------------------------------------------")
#    print(documents[i])
chroma_results=[]
for i in range(len(raw_results["ids"][0])):
    chroma_results.append({
        "id": raw_results["metadatas"][0][i]['id'],
        "source": raw_results["metadatas"][0][i]['source'],
        "page_start": raw_results["metadatas"][0][i]['page_start'],
        "page_end": raw_results["metadatas"][0][i]['page_end'],
        "text": raw_results["documents"][0][i],
        "retrieval_score": raw_results["distances"][0][i],
        "retriever": "chroma"
    })

#results=[]
#seen=set()
#for result in (bm25_results + chroma_results):
#    if result["id"] not in seen:
#        results.append(result)
#        seen.add(result["id"])
#print(len(results))

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
print(results)