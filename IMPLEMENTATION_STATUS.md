# IMPLEMENTATION_STATUS.md

_Last updated: 2025-06-08_

---

## 1. What’s Completed ✅

| Area | File(s) / Folder(s) | Functionality Provided |
|------|---------------------|------------------------|
| **Environment & Deps** | `requirements.txt` | Pin-locked Python dependencies (Flask, Supabase SDK, PDF/OCR libs, WeasyPrint, dev tools). |
| **Configuration** | `.env.example` | Template for all runtime env vars, already filled with Supabase & Sarvam placeholders. |
| **Project Skeleton** | `app/`, `tmp/`, `tests/` directories | Canonical Flask service layout plus temp folders. |
| **App Factory** | `app/__init__.py` | Creates Flask app, loads env, CORS, logging, health route. Initializes Supabase client and registers blueprints (stubs). |
| **CLI Entry** | `app/main.py` | Development server runner and WSGI entry point for Gunicorn. |
| **Supabase Service** | `app/services/supabase_client.py` | High-level wrapper around Supabase: file CRUD, job CRUD, signed URLs, storage helpers, retry util. |
| **Service Package** | `app/services/__init__.py` | Namespace for future services. |
| **Tooling** | `.pre-commit-config.yaml` | Black, isort, flake8, mypy, misc hooks already configured. |
| **Containerisation** | `Dockerfile` | Multi-stage build ‑ installs deps, Tesseract GUJ, WeasyPrint libs, non-root user, Gunicorn CMD. |
| **Directory Creation** | `mkdir` commands executed | Folders for routes, templates, static assets, etc. prepared. |

**Proof-of-life**: Hitting `GET /health` returns JSON with environment and Supabase connectivity status.

---

## 2. What’s Left to Implement 🔨

| Priority | Task | Est. Time | Depends On |
|----------|------|-----------|------------|
| **P0** | **Supabase DB schema & buckets** – run SQL below; create `uploads` & `outputs` buckets | 0.5 h | none |
| **P0** | Upload blueprint (`app/routes/upload.py`) – presigned upload URL endpoint; create file/job rows | 2 h | Supabase schema |
| **P0** | Extraction service (`app/services/extractor.py`) – pdfplumber + OCR fallback | 3 h | Tesseract installed |
| **P0** | Translation service (`app/services/translator.py`) – Sarvam API client, chunking | 2 h | Sarvam creds |
| **P0** | Job processing blueprint (`app/routes/translate.py`) – orchestrate extract→translate→build, progress updates | 3 h | previous two |
| **P0** | PDF builder service (`app/services/pdf_builder.py`) – WeasyPrint, page breaks | 2 h | extraction HTML |
| **P0** | Download blueprint (`app/routes/download.py`) – signed download URL | 1 h | Supabase buckets |
| **P1** | **ShadCN frontend** (separate `frontend/` with Vite + React + ShadCN) – upload form, progress bar (Supabase realtime), download button | 5 h | Upload & realtime events |
| **P1** | Realtime progress updates – update job row in service; client subscribes | 1 h | Supabase realtime |
| **P1** | Auth (optional) via Supabase | 2 h | frontend |
| **P2** | Tests: unit (services) & E2E happy path | 3 h | core flow |
| **P2** | CI workflow (GitHub Actions) – lint, tests, Docker build | 1 h | tests |
| **P2** | Deployment scripts (Render/Fly) | 1 h | Dockerfile |

_Total remaining core MVP effort: ~26 h_

---

## 3. ShadCN Frontend Integration 🖌️

1. **Create Frontend App**  
   ```bash
   pnpm create vite frontend --template react-ts
   cd frontend && pnpm i
   ```

2. **Install ShadCN & Tailwind**  
   ```bash
   pnpm add -D tailwindcss postcss autoprefixer
   npx shadcn-ui@latest init
   ```

3. **Core UI Components**  
   - `UploadDropzone` (uses Supabase signed URL)  
   - `ProgressBar` (subscribe to `translation_jobs` via Supabase JS)  
   - `DownloadCard` (show download link when job.status === 'done')  

4. **Connect to Backend**  
   - `VITE_API_URL=http://localhost:5000` in `.env`  
   - Axios/fetch for `/upload-url`, `/download-url/<id>`  

5. **Build & Serve**  
   - Dev: `pnpm dev` (localhost:5173)  
   - Production: `pnpm build && vite preview` or serve via Nginx; Docker multi-stage can copy `dist/` into Flask static.  

---

## 4. Updated Technology Stack 🛠️

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Flask, Gunicorn |
| Storage / DB / Auth | **Supabase** (PostgreSQL, Storage, Realtime) |
| Translation | **Sarvam AI** `/translate` API |
| OCR | Tesseract (Gujarati) |
| PDF Processing | pdfplumber, PyPDF2, pdf2image |
| PDF Generation | WeasyPrint |
| Frontend | **React + ShadCN (UI)**, Vite, Tailwind CSS |
| Tooling | Pre-commit hooks, Black, Flake8, pytest, Docker |

---

## 5. Next Steps for Cursor Development ⌨️

> Cursor will be used for all code creation & navigation.

1. **Create Supabase SQL migration** (`supabase/migrations/0001_init.sql`).  
2. **Scaffold blueprints & service stubs** in `app/routes` and `app/services`.  
3. **Implement extractor logic** – test on sample Gujarati PDF.  
4. **Write Sarvam translator client** with chunk logic + retries.  
5. **Implement job orchestration route** – update progress % to DB.  
6. **Write minimal ShadCN React app** under `frontend/`.  
7. **Wire realtime updates** – test end-to-end locally.  
8. **Add unit tests** (`tests/`).  
9. **Commit & push**; ensure pre-commit passes.  
10. **Build Docker image and run `docker compose up`** (compose file still to be created).

---

## 6. Supabase Setup Required 🗄️

### 6.1 Buckets  
```text
uploads   – private (store original PDFs)  
outputs   – private (store translated PDFs, CDN enabled)
```

### 6.2 Database Schema  
```sql
create table public.files (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id),
  original_name text not null,
  bucket text not null,
  storage_path text not null,
  created_at timestamptz default now()
);

create table public.translation_jobs (
  id uuid primary key default uuid_generate_v4(),
  file_id uuid references public.files(id) on delete cascade,
  status text default 'pending',      -- pending|processing|done|error
  progress int default 0 check (progress >= 0 and progress <= 100),
  src_lang text default 'gu',
  tgt_lang text default 'en',
  error_message text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- optional: enable Realtime
alter publication supabase_realtime add table public.translation_jobs;
```

_Disable RLS during MVP or add simple policies._

---

## 7. Current File Structure 📂

```
legalai/
├── .env.example
├── .pre-commit-config.yaml
├── Dockerfile
├── IMPLEMENTATION_STATUS.md   <- this file
├── PRD.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/               # (empty stubs)
│   ├── services/
│   │   ├── __init__.py
│   │   └── supabase_client.py
│   ├── templates/
│   └── static/
├── tmp/
│   ├── uploads/
│   └── pdfs/
└── tests/                     # to be filled
```

---

### ☑️ Summary

Core infrastructure & skeleton are in place (≈35 % done).  
Focus now shifts to implementing the functional blueprints/services and the new ShadCN React frontend, followed by tests and deployment. Estimated remaining effort: **~26 hours**.
