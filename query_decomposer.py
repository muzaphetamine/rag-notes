from llm import decompose
from query import retrieve
from query import fuse

question = input("Enter question: ")
subqueries = decompose(question)

def print_results(title, results):
    print(f"\n{'='*70}")
    print(title)
    print("="*70)

    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['retriever'].upper()}] {r['source']}  Pages {r['page_start']}-{r['page_end']}")
        print(f"   Score : {r['retrieval_score']:.4f}")
        print(f"   ID    : {r['id']}")
        print(f"   Text  : {r['text'][:150].replace('\n', ' ')}...")
        print()


all_bm25 = []
all_chroma = []
for subquery in subqueries:
    print(f"\nSubquery: {subquery}")
    bm25, chroma = retrieve(subquery)
    print_results("BM25", bm25)
    print_results("Chroma", chroma)
    all_bm25.extend(bm25)
    all_chroma.extend(chroma)

results = fuse(all_bm25, all_chroma)
#print(results)
#print(retrieve("Database Management System"))