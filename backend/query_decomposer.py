from llm import decompose, generate_answer, rerank_images
from query import retrieve, fuse, image_retrieve, fuse_multiple
import json
from pathlib import Path


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
    question_folder = Path("output/questions")
    answer_folder = Path("output/answers")
    answer_folder.mkdir(parents=True, exist_ok=True)

    question_files = list(question_folder.glob("*.json"))
    if not question_files:
        print("No question files found.")
        return

    for question_file in question_files:
        print(f"\nProcessing {question_file.name}...")
        with open(question_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
        output_file = answer_folder / question_file.name

        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                answers = json.load(f)
            completed_labels= { answer["label"] for answer in answers}
            print(f"Found {len(answers)} previously completed questions.")
        else:
            answers = []
            completed_labels = set()

        for q in questions[:6]:
            if q["label"] in completed_labels:
                print(f"Skipping {q['label']} — already completed.")
                continue
            try:
                question = q["question"]
                print(f"Processing {q['label']}...")
                subqueries = decompose(question)
                all_bm25 = []
                all_chroma = []
                image_result_sets = []
                for subquery in subqueries:
                    bm25, chroma = retrieve(subquery, k=5, n=5)
                    all_bm25.extend(bm25)
                    all_chroma.extend(chroma)
                    images = image_retrieve(subquery, n=3)
                    image_result_sets.append(images)
                results = fuse( all_bm25, all_chroma)
                image_results = fuse_multiple(image_result_sets)
                selected_ids = rerank_images(question, image_results)
                selected_images = [
                    image
                    for image in image_results
                    if image["id"] in selected_ids
                ]
                selected_images = selected_images[:2]
                answer = generate_answer(question, results)
                answers.append({
                    "label": q["label"],
                    "question": question,
                    "answer": answer,
                    "images": [
                        {
                            "text": image["text"],
                            "image_path": image["image_path"]
                        }
                        for image in selected_images
                    ]
                })

                completed_labels.add(q["label"])
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        answers,
                        f,
                        indent=4,
                        ensure_ascii=False
                    )
                print(f"Completed {q['label']} → saved.")
            except Exception as e:
                print(f"Failed question {q['label']}: {e}")
                continue

        print(f"Finished {question_file.name}")
        print(f"Saved → {output_file}")


if __name__ == "__main__":
    main()