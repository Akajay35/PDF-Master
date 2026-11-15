import io,os,zipfile,tempfile,subprocess
from pathlib import Path
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pypdf import PdfReader,PdfWriter
app=FastAPI(title="PDF Master API")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","*").split(","),allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
LIMIT=int(os.getenv("MAX_UPLOAD_MB","20"))*1024*1024
@app.get("/health")
def health(): return {"status":"ok","service":"PDF Master API"}
async def read_file(f,ext=(".pdf",)):
 name=(f.filename or "upload").lower()
 if not name.endswith(ext): raise HTTPException(400,"Unsupported file type.")
 data=await f.read()
 if not data: raise HTTPException(400,"Empty file.")
 if len(data)>LIMIT: raise HTTPException(413,"File exceeds upload limit.")
 return name,data
def send(data,name,kind="application/pdf"):
 return StreamingResponse(io.BytesIO(data),media_type=kind,headers={"Content-Disposition":f'attachment; filename="{name}"'})
@app.post("/merge")
async def merge(files:list[UploadFile]=File(...)):
 if len(files)<2: raise HTTPException(400,"Upload at least two PDFs.")
 w=PdfWriter()
 for f in files:
  _,raw=await read_file(f);r=PdfReader(io.BytesIO(raw))
  if r.is_encrypted: raise HTTPException(400,"Encrypted PDFs are not supported.")
  for p in r.pages:w.add_page(p)
 o=io.BytesIO();w.write(o);return send(o.getvalue(),"merged.pdf")
@app.post("/split")
async def split(files:list[UploadFile]=File(...)):
 if len(files)!=1: raise HTTPException(400,"Upload one PDF.")
 _,raw=await read_file(files[0]);r=PdfReader(io.BytesIO(raw))
 if r.is_encrypted: raise HTTPException(400,"Encrypted PDFs are not supported.")
 zbuf=io.BytesIO()
 with zipfile.ZipFile(zbuf,"w",zipfile.ZIP_DEFLATED) as z:
  for i,p in enumerate(r.pages,1):
   w=PdfWriter();w.add_page(p);o=io.BytesIO();w.write(o);z.writestr(f"page-{i}.pdf",o.getvalue())
 return send(zbuf.getvalue(),"split-pages.zip","application/zip")
@app.post("/compress")
async def compress(files:list[UploadFile]=File(...)):
 if len(files)!=1: raise HTTPException(400,"Upload one PDF.")
 _,raw=await read_file(files[0]);r=PdfReader(io.BytesIO(raw));w=PdfWriter()
 if r.is_encrypted: raise HTTPException(400,"Encrypted PDFs are not supported.")
 for p in r.pages:p.compress_content_streams();w.add_page(p)
 o=io.BytesIO();w.write(o);return send(o.getvalue(),"compressed.pdf")
async def convert(f,target,mime):
 name,raw=await read_file(f,(".pdf",) if target=="docx" else (".doc",".docx"))
 with tempfile.TemporaryDirectory() as d:
  src=Path(d)/name;src.write_bytes(raw);profile=Path(d)/"profile"
  result=subprocess.run(["libreoffice",f"-env:UserInstallation=file://{profile}","--headless","--convert-to",target,"--outdir",d,str(src)],capture_output=True,timeout=90)
  out=Path(d)/(src.stem+"."+target)
  if result.returncode or not out.exists():raise HTTPException(422,"Conversion failed; scanned or complex documents may need OCR.")
  return send(out.read_bytes(),out.name,mime)
@app.post("/pdf-to-word")
async def pdf_word(files:list[UploadFile]=File(...)):
 if len(files)!=1:raise HTTPException(400,"Upload one PDF.")
 return await convert(files[0],"docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
@app.post("/word-to-pdf")
async def word_pdf(files:list[UploadFile]=File(...)):
 if len(files)!=1:raise HTTPException(400,"Upload one Word document.")
 return await convert(files[0],"pdf","application/pdf")
@app.post("/rotate")
async def rotate(files:list[UploadFile]=File(...),angle:int=Form(90)):
 if len(files)!=1 or angle not in (90,180,270):raise HTTPException(400,"Upload one PDF and choose 90, 180 or 270 degrees.")
 _,raw=await read_file(files[0]);r=PdfReader(io.BytesIO(raw));w=PdfWriter()
 if r.is_encrypted:raise HTTPException(400,"Encrypted PDFs are not supported.")
 for p in r.pages:p.rotate(angle);w.add_page(p)
 o=io.BytesIO();w.write(o);return send(o.getvalue(),"rotated.pdf")
@app.post("/protect")
async def protect(files:list[UploadFile]=File(...),password:str=Form(...)):
 if len(files)!=1 or len(password)<4:raise HTTPException(400,"Upload one PDF and use a password of at least 4 characters.")
 _,raw=await read_file(files[0]);r=PdfReader(io.BytesIO(raw));w=PdfWriter()
 if r.is_encrypted:raise HTTPException(400,"This PDF is already encrypted.")
 w.append_pages_from_reader(r);w.encrypt(password);o=io.BytesIO();w.write(o);return send(o.getvalue(),"protected.pdf")
