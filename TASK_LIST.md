# TASK_LIST.md
Comprehensive roadmap for completing **LegalAI – Gujarati Legal Document Translator**.  
Priority scale: **P0 (blocker) → P3 (nice-to-have)**.  
✅ DONE = task finished in current code-base.

| Pri | Area | Task | Details & Acceptance Criteria | Est. (h) | Status / Depends On |
|-----|------|------|------------------------------|----------|----------------------|
| **P0** | **Security** | Sanitize Sarvam API key | Replace real key in repo & purge history | 1 | ⬜ TODO |
| **P0** | **Security** | Sanitize Supabase credentials | Replace real keys & purge history | 1 | ⬜ TODO |
| **P0** | **Security** | Rotate exposed credentials | Generate new keys, update secrets | 0.5 | ⬜ TODO |
| **P0** | **Security** | Secret-scanning in CI | Add detect-secrets / truffleHog step | 1 | ⬜ TODO |
| **P0** | **Security** | Update pre-commit hooks | `pre-commit autoupdate`, add detect-secrets | 0.5 | ⬜ TODO |
| **P0** | **Backend** | Supabase DB schema & buckets | Run `supabase_schema.sql`, create `uploads` & `outputs` buckets | 0.5 | ⬜ TODO |
| **P0** | **Backend** | Upload blueprint | `/api/upload/*` endpoints, unit tests | 2 | ✅ DONE |
| **P0** | **Backend** | Extraction service | `app/services/extractor.py` finished | 3 | ✅ DONE |
| **P0** | **Backend** | Translation service | `app/services/translator.py` finished | 2 | ✅ DONE |
| **P0** | **Backend** | Job orchestrator route | `app/routes/translate.py` finished | 3 | ✅ DONE |
| **P0** | **Backend** | PDF builder service | `app/services/pdf_builder.py` finished | 2 | ✅ DONE |
| **P0** | **Backend** | Download blueprint | `app/routes/download.py` finished | 1 | ✅ DONE |
| **P0** | **Quality** | Smoke test script | End-to-end script uploads sample & downloads PDF | 1 | ⬜ TODO |
| **P1** | **Frontend / bolt.new** | Generate UI components with bolt.new | Prompts documented in `FRONTEND_USER_FLOW.md`; components: UploadDropzone, ModalProgress, JobStatusCard, DownloadCard | 3 | ⬜ TODO |
| **P1** | **Frontend / bolt.new** | Integrate bolt-generated React app | Vite+TS project in `frontend/`, connect to backend APIs, env `VITE_API_URL` | 4 | ⬜ TODO |
| **P1** | **Frontend** | Realtime progress UI | Supabase Realtime subscription (or polling fallback) | 1 | ⬜ TODO |
| **P1** | **Infra** | GitHub Actions CI | Lint, unit tests, smoke test, secret scan, Docker build | 2 | ⬜ TODO |
| **P1** | **Infra** | Docker Compose / Devcontainer | Local stack with Supabase emulator | 1.5 | ⬜ TODO |
| **P2** | **Testing** | Unit tests for services | extractor, translator (mock), supabase client; ≥80 % coverage | 3 | ⬜ TODO |
| **P2** | **Testing** | E2E tests (Playwright) | Full web flow incl. frontend | 2 | ⬜ TODO |
| **P2** | **Deployment** | Cloud deploy scripts | Render/Fly, healthchecks, secrets | 1 | ⬜ TODO |
| **P2** | **Security** | HTTPs, CORS hardening, rate-limit | flask-limiter, proxy config | 1 | ⬜ TODO |
| **P2** | **Docs** | Update README & diagrams | Env var table, sequence diagram, security policy | 1 | ⬜ TODO |
| **P3** | **Enhancement** | Advanced formatting retention | Tables, styles, pdfminer layout | 4 | ⬜ TODO |
| **P3** | **Enhancement** | Batch translations | Multi-file jobs, parallel queue | 3 | ⬜ TODO |
| **P3** | **Feature** | Glossary / terminology override | CSV import, translator substitution | 3 | ⬜ TODO |
| **P3** | **Feature** | Auth & RLS policies | Supabase Auth, row-level security | 2 | ⬜ TODO |
| **P3** | **Ops** | Monitoring & tracing | Prometheus/Grafana, Sentry | 2 | ⬜ TODO |

---

## Progress Summary
Backend core workflow—upload ➜ extract ➜ translate ➜ build PDF ➜ download—**fully implemented (6 / 7 P0 backend items)**.  
Frontend not yet generated; bolt.new prompts & user flow doc created.  
Overall MVP completion ≈ **60 %** (backend done, security & frontend pending).  
Next critical steps: **security cleanup**, apply Supabase schema, generate bolt.new frontend, integrate & smoke-test.
