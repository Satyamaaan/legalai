# TASK_LIST.md
Comprehensive roadmap for completing **LegalAI – Gujarati Legal Document Translator**.  
Priorities follow the scale: **P0 (blocker / must-fix before next commit) → P3 (nice-to-have after MVP).**  
All estimates are optimistic engineering‐hours of focused work.

| Pri | Area | Task | Details & Acceptance Criteria | Est. (h) | Depends On |
|-----|------|------|------------------------------|----------|------------|
| **P0** | **Security** | Sanitize Sarvam API key | Remove real key from `.env.example`; replace with `your-sarvam-api-key`. Verify history: purge via [GitHub BFG / filter-repo] and force-push. | 1 | — |
| **P0** | **Security** | Sanitize Supabase credentials (occurs twice) | Replace real `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` in `.env.example` with placeholders; purge from git history. | 1 | — |
| **P0** | **Security** | Rotate exposed credentials | Generate new keys in Supabase & Sarvam portals; update deployment secrets (Render/Fly/CI). | 0.5 | previous two |
| **P0** | **Security** | Add secret-scanning to CI | Enable GitHub Advanced Security or use `truffleHog` pre-commit + CI step. Fails pipeline on secrets. | 1 | CI pipeline in place |
| **P0** | **Security** | Update `.pre-commit-config.yaml` hooks | Bump hook versions; ensure `detect-secrets` hook added; run `pre-commit autoupdate`. | 0.5 | — |
| **P0** | **Backend** | Supabase DB schema & buckets | Apply `supabase_schema.sql`; create `uploads` & `outputs` buckets. | 0.5 | Supabase project |
| **P0** | **Backend** | Upload blueprint (`app/routes/upload.py`) | Endpoint: returns signed upload URL; inserts file + job rows. Unit tests. | 2 | schema |
| **P0** | **Backend** | Extraction service (`extractor.py`) | pdfplumber + OCR fallback; returns HTML/text blocks with basic structure. | 3 | Tesseract installed |
| **P0** | **Backend** | Translation service (`translator.py`) | Sarvam API client, chunking ≤1000 chars, retries. | 2 | Sarvam creds secured |
| **P0** | **Backend** | Job orchestrator route (`translate.py`) | Flow: extract → translate → build; update progress to DB. | 3 | extractor, translator |
| **P0** | **Backend** | PDF builder service (`pdf_builder.py`) | Convert translated HTML to paginated PDF via WeasyPrint. | 2 | extractor output |
| **P0** | **Backend** | Download blueprint (`download.py`) | Returns signed download URL for finished PDF. | 1 | buckets, builder |
| **P0** | **Quality** | Smoke test script | CLI/E2E script that uploads sample PDF and downloads output; must pass in CI. | 1 | all core flow |
| **P1** | **Frontend** | Scaffold ShadCN React app | Vite+TS; env var `VITE_API_URL`; basic pages. | 5 | upload endpoint |
| **P1** | **Frontend** | Realtime progress UI | Supabase JS subscribe to `translation_jobs`; show progress bar. | 1 | Supabase realtime |
| **P1** | **Frontend** | Download component | Poll /subscribe until status `done`; link to signed URL. | 0.5 | download route |
| **P1** | **Infra** | GitHub Actions CI | Jobs: lint (black, flake8, mypy), unit tests, smoke test, secret scan, Docker build. | 2 | tests, secret-scan |
| **P1** | **Infra** | Docker Compose / Devcontainer | One-shot stack: Flask + Postgres + Supabase local emulator. Docs in README. | 1.5 | core services |
| **P2** | **Testing** | Unit tests for services | extractor, translator (mock), supabase client. Coverage ≥80 %. | 3 | services complete |
| **P2** | **Testing** | E2E tests with Playwright | Headless run of full web flow. | 2 | frontend stable |
| **P2** | **Deployment** | Render/Fly deploy workflows | IaC scripts, build args for secrets, healthchecks. | 1 | CI Docker |
| **P2** | **Security** | HTTPs, CORS hardening, Rate-limit | Use proxy /gunicorn middlewares, flask-limiter. | 1 | deployment |
| **P2** | **Docs** | Update README & Architecture diagram | Include env var table, sequence diagram, security policy. | 1 | MVP stable |
| **P3** | **Enhancement** | Advanced formatting retention | Tables, lists, styles; evaluate pdfminer.six layout. | 4 | MVP feedback |
| **P3** | **Enhancement** | Batch translations | Multiple files per job; parallel processing queue. | 3 | core flow |
| **P3** | **Feature** | Glossary / terminology override | Simple CSV upload; translator substitutes terms. | 3 | translator refactor |
| **P3** | **Feature** | Auth & RLS policies | Enable Supabase Auth; apply SQL policies; lock buckets. | 2 | frontend auth |
| **P3** | **Ops** | Monitoring + tracing | Prometheus metrics, Grafana dashboard, Sentry errors. | 2 | deployment |

---

## Critical-Path Order (high-level)
1. **Security cleanup & credential rotation**  
2. Apply DB schema → implement core backend services/routes → smoke test.  
3. Frontend scaffold & realtime integration.  
4. CI/CD, testing, deployment.  
5. Nice-to-have enhancements post-MVP.

Total core MVP effort (P0 + P1): **≈24 h** (excludes coordination).  
Security tasks must be completed **before any public commits or deployments**.
