from llm import decompose
from query import retrieve
from query import fuse


def print_results(title, results):
    print(f"\n{'='*70}")
    print(title)
    print("="*70)

    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['retriever'].upper()}] {r['source']}  Heading {r['heading']}")
        print(f"   Score : {r['retrieval_score']:.4f}")
        print(f"   ID    : {r['id']}")
        print(f"   Text  : {r['text'].replace('\n', ' ')}")
        print()


def main():
    question = input("Enter question: ")
    subqueries = decompose(question)

    all_bm25 = []
    all_chroma = []
    for subquery in subqueries:
        print(f"\nSubquery: {subquery}")
        bm25, chroma = retrieve(subquery,  k=10, n=10)
        print_results("BM25", bm25)
        print_results("Chroma", chroma)
        all_bm25.extend(bm25)
        all_chroma.extend(chroma)

    results = fuse(all_bm25, all_chroma)
    #print(results)
    #print(retrieve("Database Management System"))


if __name__ == "__main__":
    main()