import nltk
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import re
import json
from pathlib import Path


nltk.download('punkt_tab')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def valid(sent):
    MIN_WORDS = 4 
    MAX_DIGIT_RATIO = 0.3
    if len(sent.split()) < MIN_WORDS:
        return False
    if re.match(r'^Page\s+\d+$', sent.strip()):
        return False
    digit_count = sum(c.isdigit() for c in sent)
    if len(sent) > 0 and (digit_count / len(sent)) > MAX_DIGIT_RATIO:
        return False
    return True


def chunk(txt_file):
    Path("output/chunks").mkdir(parents=True, exist_ok=True)
    with open(txt_file, "r", encoding="utf-8") as file:
        content=file.read().split('\x0c')
        file_name = txt_file.stem

        page_index=1
        sent_list=[]
        for page_content in content:
            sentences=nltk.sent_tokenize(page_content)
            for sent in sentences:
                if valid(sent): sent_list.append((sent,page_index))
            page_index+=1


        raw_sent_list=[sent for sent,page_index in sent_list]
        if not raw_sent_list:
            #print(f"No valid sentences in {txt_file.name}")
            return
        embeddings=model.encode(raw_sent_list)
        embed_list=list(zip(sent_list,embeddings))


        chunks=[]
        current_chunk=[]
        centroid=None
        threshold=0.45
        for (sent, page_index),embedding in embed_list:
            if not current_chunk:
                current_chunk.append((sent, page_index, embedding))
                centroid=embedding
                continue
            similarity=np.dot(embedding,centroid)/(np.linalg.norm(embedding)*np.linalg.norm(centroid))
            if similarity >= threshold:
                current_chunk.append((sent, page_index, embedding))
                centroid=np.mean(np.array([e for _,_,e in current_chunk]),axis=0)
            else:
                chunks.append({
                    "source": file_name,
                    "text":" ".join([sent for sent,_,_ in current_chunk]),
                    "pages": [page for _,page,_ in current_chunk],
                    "centroid": centroid.tolist()
                })
                current_chunk=[(sent, page_index, embedding)]
                centroid=embedding
        if current_chunk:
            chunks.append({
                        "source": file_name,
                        "text":" ".join([sent for sent,_,_ in current_chunk]),
                        "pages": [page for _,page,_ in current_chunk],
                        "centroid": centroid.tolist()
                    })
        
        output_file = Path("output/chunks") / f"{file_name}_chunks.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=4, ensure_ascii=False)

        print("we have these many chunks: ", len(chunks))
        print("total sentences: ", len(sent_list))
        print(f"Saved to {output_file}")




text_folder = Path("output/text")

for txt_file in text_folder.glob("*.txt"):
    try:
        print(f"Processing {txt_file.name}")
        chunk(txt_file)
    except Exception as e:
        print(f"✗ Failed on {txt_file.name}: {e}")

print("Done!")