from extract_docling import process_extraction
from chunk_docling import process_chunking
from store import process_store
from query_decomposer import process_questions
from generate_pdf import process_pdfs


def run_pipeline(progress_callback=None):
    process_extraction(progress_callback)
    process_chunking(progress_callback)
    process_store(progress_callback)
    process_questions(progress_callback)
    process_pdfs(progress_callback)


def main():
    run_pipeline()


if __name__ == "__main__":
    main()