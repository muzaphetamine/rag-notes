import nltk
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import re
import json
import re
from pathlib import Path

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
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
        content=file.read()
        file_name = txt_file.stem
        sections = re.split(r'(?m)^(#{1,6})\s+(.+)$', content)
        sent_list=[]

        current_heading = ""
        for i in range(1, len(sections), 3):
            heading_level = sections[i]
            heading = sections[i + 1].strip()
            section_content = sections[i + 2]
            current_heading = heading
            sentences = nltk.sent_tokenize(section_content)
            for sent in sentences:
                if valid(sent):
                    sent_list.append((sent, current_heading))

        raw_sent_list=[sent for sent, heading in sent_list]
        if not raw_sent_list:
            return
        embeddings=model.encode(raw_sent_list)
        embed_list=list(zip(sent_list,embeddings))

        chunks=[]
        current_chunk=[]
        current_word_count =0
        chunk_num=1
        centroid=None
        threshold=0.45
        MAX_WORDS=150
        for (sent, heading),embedding in embed_list:
            if not current_chunk:
                current_chunk.append((sent, heading, embedding))
                current_word_count=len(sent.split())
                centroid=embedding
                continue
            similarity=np.dot(embedding,centroid)/(np.linalg.norm(embedding)*np.linalg.norm(centroid))
            new_word_count = len(sent.split())
            if similarity >= threshold and current_word_count + new_word_count <= MAX_WORDS:
                current_chunk.append((sent, heading, embedding))
                current_word_count +=new_word_count
                centroid=np.mean(np.array([e for _,_,e in current_chunk]),axis=0)
            else:
                chunks.append({
                    "id": f"{file_name}_{chunk_num}",
                    "source": file_name,
                    "text":" ".join([sent for sent,_,_ in current_chunk]),
                    "heading": current_chunk[0][1],
                    "centroid": centroid.tolist()
                })
                chunk_num+=1
                current_chunk=[(sent, heading, embedding)]
                current_word_count= new_word_count
                centroid=embedding
        if current_chunk:
            chunks.append({
                        "id": f"{file_name}_{chunk_num}",
                        "source": file_name,
                        "text":" ".join([sent for sent,_,_ in current_chunk]),
                        "heading": current_chunk[0][1],
                        "centroid": centroid.tolist()
                    })
            chunk_num+=1
        
        output_file =Path("output/chunks") / f"{file_name}_chunks.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=4, ensure_ascii=False)
        print("we have these many chunks: ", len(chunks))
        print("total sentences: ", len(sent_list))
        print(f"Saved to {output_file}")


def main():
    text_folder = Path("output/md")
    for txt_file in text_folder.glob("*.md"):
        try:
            print(f"Processing {txt_file.name}")
            chunk(txt_file)
        except Exception as e:
            print(f"✗ Failed on {txt_file.name}: {e}")
    print("Done!")


if __name__ == "__main__":
    main()