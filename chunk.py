import nltk
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import re


nltk.download('punkt_tab')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


path="output.txt"
file=open(path, 'r', encoding='utf-8')
content=file.read().split('\x0c')
#for i in range(4):
#    print(content[i])
#    print("\n-------I wrote this line as page separator------\n")


def valid(sent):
    MIN_WORDS = 4 
    MAX_DIGIT_RATIO = 0.3
    # Rule 1: too short to be real content
    if len(sent.split()) < MIN_WORDS:
        return False
    # Rule 2: standalone "Page N" artifact
    if re.match(r'^Page\s+\d+$', sent.strip()):
        return False
    # Rule 3: too many digits relative to length (catches chapter/reference listings)
    digit_count = sum(c.isdigit() for c in sent)
    if len(sent) > 0 and (digit_count / len(sent)) > MAX_DIGIT_RATIO:
        return False
    return True


page_index=1
sent_list=[]
for page_content in content:
    sentences=nltk.sent_tokenize(page_content)
    for sent in sentences:
        if valid(sent): sent_list.append((sent,page_index))
    page_index+=1
#for i in range(6):
#    print(sent_list[i])
#    print("\n-------I wrote this line as sentence separator------\n")


raw_sent_list=[sent for sent,page_index in sent_list]
embeddings=model.encode(raw_sent_list)
embed_list=list(zip(sent_list,embeddings))
#for i in range(6):
#    print(embed_list[i])
#    print("\n-------I wrote this line as sentence separator------\n")

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
            "text":" ".join([sent for sent,_,_ in current_chunk]),
            "pages": [page for _,page,_ in current_chunk],
            "centroid": centroid
        })
        current_chunk=[(sent, page_index, embedding)]
        centroid=embedding
if current_chunk:
    chunks.append({
                "text":" ".join([sent for sent,_,_ in current_chunk]),
                "pages": [page for _,page,_ in current_chunk],
                "centroid": centroid
            })
print("we have these many chunks: ", len(chunks))
print("total sentences: ", len(sent_list))
#for i in range(3):
#    print(chunks[i])
#    print("\n-------I wrote this line as chunk separator------\n")
#print(chunks[2]["text"])
#print("\n-------I wrote this line as chunk separator------\n")
#print(chunks[14]["text"])
#print("\n-------I wrote this line as chunk separator------\n")
#print(chunks[77]["text"])
#print("\n-------I wrote this line as chunk separator------\n")
#print(chunks[136]["text"])
#print("\n-------I wrote this line as chunk separator------\n")