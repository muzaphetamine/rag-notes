import pymupdf
import json
doc=pymupdf.open("samples/dbms1.pdf")
out=open("output.txt","wb")
imgfile=open("images/images.txt","wb")
imgdict={}
N=1
for page in doc:
    index=1
    text=page.get_text().encode("utf8")
    imgs=page.get_images()
    for img in imgs:
        xref=img[0]
        data=doc.extract_image(xref)
        filename=f"images/page{N}_img{index}.{data['ext']}"
        with open(filename, "wb") as f:
            f.write(data["image"])
        imgdict.setdefault(N, []).append(filename)
        index+=1
    out.write(text)
    out.write(bytes((12,)))
    N+=1
with open("img_data.json","w") as f:
    json.dump(imgdict,f,indent=4)
imgfile.close()
out.close()