# PDF Master

A responsive PDF utility website built with Next.js and a FastAPI processing service.

## Working tools
- Merge multiple PDFs
- Split a PDF into page files (ZIP)
- Optimize PDF content streams
- PDF to Word (DOCX) and Word to PDF using LibreOffice
- Rotate PDF pages
- Protect PDFs with a password

The PDF-to-Images tile is marked as coming soon and is not connected yet.

## Run locally

Frontend:
```bash
npm install
```
Create `.env.local` in the project root:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
Then run `npm run dev`.

Backend (Python 3.12 and LibreOffice Writer required):
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Health check: `http://localhost:8000/health`.

## Deploy
1. Import this repository into Vercel as a Next.js project (root directory: `.`).
2. Deploy the backend folder as a Docker web service (the included `render.yaml` is a starting point).
3. Add `NEXT_PUBLIC_API_URL` to Vercel with the backend's public base URL, then redeploy the frontend.
4. Replace the backend's `CORS_ORIGINS=*` with your exact frontend origin before public launch.

Free hosting may sleep and has CPU, memory, and request limits. PDF-to-Word quality depends on the document; scanned PDFs need OCR, which is not included. Compression optimizes content streams and will not shrink every file. The service processes files in memory or a temporary directory and does not intentionally save them, but hosting providers may have their own logs and temporary storage policies. Do not upload confidential documents until you review provider privacy and security settings.
