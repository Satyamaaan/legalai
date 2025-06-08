# LegalAI – Gujarati PDF Translation Service

A full-stack web application that lets users upload Gujarati legal PDFs, automatically extracts and translates the content to English using Sarvam AI, and returns a structurally-similar translated PDF.  
The stack is **Flask + Supabase (PostgreSQL / Storage / Realtime) + Sarvam AI + ShadCN UI (React)**.  
The goal is to remove manual, error-prone legal translation work while preserving document layout.

---

## 1 · Current Status 🚦

| Area | ✅ Done | 🔨 Left |
|------|--------|--------|
| **Repo Skeleton** | Flask app factory, logging, env loader, folder structure | — |
| **Supabase Client** | High-level wrapper (`supabase_client.py`) | — |
| **Dockerfile** | Multi-stage, Tesseract + WeasyPrint ready | — |
| **Dev Tooling** | `requirements.txt`, pre-commit, Black, Flake8 | — |
| **Extraction Service** | `extractor.py` (pdfplumber, PyPDF2, OCR fallback) | Edge cases tuning |
| **Translation Service** | `translator.py` (Sarvam chunking, HTML preserve) | Unit tests |
| **Upload Blueprint** | Presigned URL + DB rows | Translate & Download blueprints |
| **DB Schema** | `supabase_schema.sql` (files, translation_jobs, realtime) | Execute on Supabase |
| **Frontend** | — | ShadCN React app with progress & download UI |
| **Tests / CI / Deploy** | — | To be added |

---

## 2 · Local Development Setup 🛠️

```bash
# 1. Clone and enter
git clone https://github.com/your-org/legalai.git
cd legalai

# 2. Python 3.11 virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Copy env template and fill keys
cp .env.example .env
#   • SECRET_KEY, SUPABASE_URL, SUPABASE_* keys, SARVAM_API_KEY …

# 5. Install Tesseract GUJ if missing (macOS example)
brew install tesseract
brew install tesseract-lang  # ensure guj traineddata present
```

---

## 3 · Supabase Setup 📦

1. **Create Project** at https://app.supabase.com  
2. **Buckets** → Storage  
   * `uploads`  (private)  
   * `outputs` (private + CDN)  
3. **Database** → SQL Editor → run `supabase_schema.sql` from repo  
4. **Realtime** is enabled by the SQL script (publication `supabase_realtime`)  
5. **Keys**: copy **Anon** and **Service role** into `.env`  

_No Row-Level Security during MVP; enable later._

---

## 4 · Environment Configuration 🔑

`.env` (see `.env.example`):

```
# Flask
FLASK_APP=app.main:create_app
FLASK_ENV=development
SECRET_KEY=replace-me

# Limits
MAX_CONTENT_LENGTH=20971520  # 20 MB

# Supabase
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
UPLOADS_BUCKET=uploads
OUTPUTS_BUCKET=outputs

# Sarvam AI
SARVAM_API_KEY=sk_...
SARVAM_API_URL=https://api.sarvam.ai/v1
SARVAM_MAX_CHARS=1000

# OCR
TESSERACT_PATH=/usr/bin/tesseract
```

---

## 5 · Running the Application ▶️

### Backend (Flask)

```bash
# Dev server
python -m app.main --host 0.0.0.0 --port 5000 --debug
# Health check
curl http://localhost:5000/health
```

### Frontend (ShadCN – to be generated)

```bash
cd frontend
pnpm i
pnpm dev      # http://localhost:5173
```

---

## 6 · Next Steps in Cursor ⌨️

1. **Execute `supabase_schema.sql`** and create buckets.  
2. Implement remaining blueprints: `translate.py`, `download.py`.  
3. Build **`frontend/`** with Vite + React + ShadCN:  
   * `UploadDropzone`, `ProgressBar` (Supabase Realtime), `DownloadCard`.  
4. Wire progress updates – update `translation_jobs.progress` in services.  
5. Add unit tests (`pytest`) and E2E smoke test.  
6. Set up GitHub Actions for lint + tests.  
7. Deploy container to Render/Fly.

_Browse **IMPLEMENTATION_STATUS.md** for detailed task list and estimates._

---

## 7 · API Basics 🌐

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/presigned-url` | Get presigned URL + `job_id` (see JSON body in code). |
| `POST` | `/api/upload/validate` | Validate filename/size before requesting URL. |
| `POST` | `/api/translate/<job_id>` _(todo)_ | Start extraction→translation pipeline. |
| `GET`  | `/api/download/<job_id>` _(todo)_ | Obtain signed download URL for translated PDF. |
| `GET`  | `/health` | Liveness probe. |

_All other data is managed via Supabase `files` and `translation_jobs` tables._

---

## 8 · Key Dependencies 📚

* **Flask 2.3** – web framework  
* **supabase-py 2.x** & **storage3** – DB / Storage / Realtime  
* **pdfplumber / PyPDF2** – searchable PDF extraction  
* **pytesseract + pdf2image** – Gujarati OCR fallback  
* **WeasyPrint 60** – HTML → PDF rendering  
* **requests / bs4** – HTTP & HTML manipulation  
* **ShadCN UI** – React component library (post-MVP)  
* Dev: **Black, Flake8, pytest, pre-commit**  

---

## 9 · Docker Compose / Container 🐳

The provided `Dockerfile` builds a slim image with:

* Python 3.11-slim  
* Tesseract + Gujarati traineddata  
* Poppler utils (pdf2image)  
* WeasyPrint runtime libs  
* Runs Gunicorn on port `8000`

Build & run:

```bash
docker build -t legalai:latest .
docker run --env-file .env -p 8000:8000 legalai:latest
```

_Add a `docker-compose.yml` later to orchestrate Flask + frontend + (optionally) PostgREST if mirroring Supabase API locally._

---

## 10 · Contributing 🤝

1. Create feature branch  
2. Ensure `pre-commit` passes (`pre-commit run --all-files`)  
3. Write/maintain tests  
4. Submit PR with context link to **IMPLEMENTATION_STATUS.md**

---

### License

MIT © 2025 LegalAI team
