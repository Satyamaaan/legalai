# FRONTEND_USER_FLOW.md
LegalAI · Front-End User Flow & Bolt Prompts  
_(target stack: Vite + React + TypeScript + Tailwind + ShadCN/UI, generated via [bolt.new](https://bolt.new))_

---

## 1. Product Context
The web app lets users upload Gujarati legal PDFs, tracks OCR → translation → PDF-build progress, and returns a translated PDF.  
Back-end endpoints (already implemented):

| Purpose | Method & Path | Notes |
|---------|---------------|-------|
| Generate signed upload URL | `POST /api/upload/signed-url` | returns `upload_url`, `file_id`, `job_id` |
| Confirm upload | `POST /api/upload/confirm` | body: `{ job_id }` |
| Poll job status | `GET  /api/upload/status/:job_id` | fields: `status`, `progress` |
| Start translation | `POST /api/translate/start/:job_id` |
| Download translated PDF | `GET  /api/download/job/:job_id?redirect=true` |
| Health checks | `/health`, `/api/*/health` |

---

## 2. Primary Persona & Goals
*“Riya”, paralegal*  
• Quickly translate Gujarati FIRs/contracts to English.  
• Needs drag-and-drop upload, live progress bar, and one-click download.  

---

## 3. High-Level Journey Map

| Step | UI Page / Component | Backend Interaction | Success Criteria |
|------|--------------------|---------------------|------------------|
| 1. Landing | LandingPage → UploadDropzone | none | PDF file accepted |
| 2. Upload | UploadDropzone → shows ModalProgress | `signed-url`, direct PUT to Supabase Storage → `confirm` | File uploaded, job created |
| 3. Processing | JobStatusCard + ProgressBar | Poll `status` every 3 s | Progress reaches 100 % |
| 4. Translation | Trigger Translate action | `translate/start` → continues polling | Status =`done` |
| 5. Download | DownloadCard | `download/job?redirect=true` | PDF opens / saves |
| 6. History (optional) | HistoryPage | Query Supabase `translation_jobs` (future) | Past jobs visible |

---

## 4. Detailed Flow Description
1. **User selects / drags PDF** → `UploadDropzone` validates extension ≤ 20 MB.  
2. `signed-url` API returns creds → front-end performs `PUT` directly to Supabase Storage.  
3. After success, front-end hits `upload/confirm` (5 % progress) then immediately calls `translate/start` (10 %).  
4. `JobStatusCard` begins polling `/status/:job_id` (or subscribe via Supabase Realtime).  
5. UI updates **ProgressBar**. Stages: extracting (15–40 %), translating (40–70 %), building (70–100 %).  
6. When status =`done`, **DownloadCard** renders “Download PDF” button linking to `download/job/:job_id?redirect=true`.  
7. User downloads file; toast shows completion.  

Error states: upload failure, API 500, translation error (status =`error`, show message & retry button).

---

## 5. Component Catalog & Bolt Prompts

> ⚡ **How to use**: open https://bolt.new → paste the prompt → copy generated code into `frontend/src/components`.

### 5.1 UploadDropzone
**Purpose**: drag-and-drop or click to choose PDF.

**Bolt Prompt**

```
Generate a React + TypeScript component named UploadDropzone using shadcn/ui and tailwind.
Requirements:
- Accept only .pdf, max 20 MB.
- Shows dashed border area with icon.
- On file select, call onFileAccepted(File) prop.
- Display error toast via shadcn/toast if validation fails.
- Fully responsive, center content.
```

**Props**
```ts
interface UploadDropzoneProps {
  onFileAccepted: (file: File) => void;
}
```

### 5.2 ModalProgress
Shows modal with animated ProgressBar & status text.

Prompt:

```
Create ModalProgress component:
- Uses Dialog from shadcn/ui.
- Props: open:boolean, progress:number 0-100, stage:string.
- Indeterminate bar when progress = 0.
- Centered in viewport.
```

### 5.3 JobStatusCard
Displays current job info.

Prompt:

```
React TS component JobStatusCard:
- Accepts job:{id,status,progress,error_message?}
- Renders ProgressBar, status badge (color coded), retry button if error.
- Uses Card, Progress from shadcn/ui.
```

### 5.4 DownloadCard
Prompt:

```
Component DownloadCard:
- Props: downloadUrl:string, filename:string.
- Show success icon, file name, "Download" button.
- Button uses link target="_blank".
```

### 5.5 HistoryPage *(future)*
Prompt:

```
Create HistoryPage:
- Fetch /api/upload/history (placeholder) on mount.
- Table of jobs with columns: date, original file, status, action buttons.
```

---

## 6. Integration Instructions

### 6.1 Project Scaffold

```
pnpm create vite frontend --template react-ts
cd frontend
pnpm i
pnpm add @tanstack/react-query axios shadcn-ui
npx shadcn-ui@latest init
```

### 6.2 Environment Variables

`frontend/.env`:

```
VITE_API_URL=http://localhost:5000
```

### 6.3 API Utility (`src/lib/api.ts`)

```ts
import axios from "axios";
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

export const getSignedUrl = (filename:string) =>
  api.post("/api/upload/signed-url",{ filename, content_type:"application/pdf"});

export const confirmUpload = (job_id:string) =>
  api.post("/api/upload/confirm",{ job_id });

export const startTranslate = (job_id:string) =>
  api.post(`/api/translate/start/${job_id}`);

export const getStatus = (job_id:string) =>
  api.get(`/api/upload/status/${job_id}`);

export const getDownloadUrl = (job_id:string) =>
  api.get(`/api/download/job/${job_id}`,{ params:{ redirect:false }});
```

### 6.4 Upload Flow in Frontend

```ts
const handleFile = async (file: File) => {
  const { data } = await getSignedUrl(file.name);
  await fetch(data.upload_url, { method:"PUT", body:file }); // direct upload
  await confirmUpload(data.job_id);
  await startTranslate(data.job_id);
  setJobId(data.job_id);
};
```

### 6.5 Polling for Progress

```ts
useEffect(() => {
  if(!jobId) return;
  const id = setInterval(async ()=>{
     const { data } = await getStatus(jobId);
     setJob(data);
     if(data.status==="done" || data.status==="error") clearInterval(id);
  }, 3000);
  return () => clearInterval(id);
},[jobId]);
```

### 6.6 Download Action

```ts
const download = async () => {
  const { data } = await getDownloadUrl(job.id);
  window.open(data.download_url, "_blank");
};
```

### 6.7 CORS / Port
Backend allows `http://localhost:5001` (adjust in `.env`).  
Run frontend on port `5001`:

```
pnpm dev --port 5001
```

---

## 7. Future Enhancements
1. Replace polling with Supabase Realtime on `translation_jobs` updates.  
2. Add authentication (Supabase Auth) for job history per user.  
3. File preview viewer (PDF.js) side-by-side original + translation.

---

## 8. Bolt Workflow Checklist

| Component | Paste Prompt | Copy Code → `frontend/src/components` | Adjust props if needed |
|-----------|--------------|---------------------------------------|------------------------|
| UploadDropzone | ✅ | ✅ | ✅ |
| ModalProgress | ✅ | ✅ | ✅ |
| JobStatusCard | ✅ | ✅ | ✅ |
| DownloadCard | ✅ | ✅ | ✅ |
| HistoryPage | (future) |   |   |

---

Happy coding! 🚀
