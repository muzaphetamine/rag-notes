import os
os.environ["TORCHINDUCTOR_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("input/dbms1_first5.pdf")
print(result.document.export_to_markdown())