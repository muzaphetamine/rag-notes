import pymupdf
import json
from pathlib import Path

def extract(pdf_file):
    pdf_name=pdf_file.stem
    Path("output/text").mkdir(parents=True, exist_ok=True)
    Path(f"output/images/{pdf_name}").mkdir(parents=True, exist_ok=True)
    image_dir = Path("output/images")/pdf_name
    with pymupdf.open(pdf_file) as doc:
        with open(f"output/text/{pdf_name}.txt","wb") as out:
            imgdict={}
            page_num=1
            for page in doc:
                img_num=1
                text=page.get_text().encode("utf8")
                imgs=page.get_images()
                for img in imgs:
                    xref=img[0]
                    data=doc.extract_image(xref)
                    image_path = image_dir/f"page{page_num}_img{img_num}.{data['ext']}"
                    with open(image_path, "wb") as f:
                        f.write(data["image"])
                    relative_path = str(Path(pdf_name)/image_path.name)
                    imgdict.setdefault(page_num, []).append(relative_path)
                    img_num+=1
                out.write(text)
                out.write(bytes((12,)))
                page_num+=1
            with open(image_dir/"img_data.json", "w") as f:
                json.dump(imgdict, f, indent=4)


input_folder = Path("input")

for pdf_file in input_folder.glob("*.pdf"):
    try:
        print(f"Processing {pdf_file.name}...")
        extract(pdf_file)
    except Exception as e:
        print(f"✗ Failed on {pdf_file.name}: {e}")

print("Done!")
