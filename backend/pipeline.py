from extract_docling import process_extraction
from chunk_docling import process_chunking
from store import process_store
from query_decomposer import process_questions
from generate_pdf import process_pdfs
from llm import configure


def run_pipeline(api_key=None, rpm=None, model=None, progress_callback=None):
    configure(api_key=api_key,rpm=rpm,model=model)
    process_extraction(progress_callback=progress_callback)
    process_chunking(progress_callback=progress_callback)
    process_store(progress_callback=progress_callback)
    process_questions(progress_callback=progress_callback)
    process_pdfs(progress_callback=progress_callback)


def main():
    run_pipeline()


if __name__ == "__main__":
    main()