# AGENTS.md — Tripo3D MVP

Instructions for any coding agent (Jules, OpenCode, Hermes, Grok Bot, Claude, Codex, …) working in this repository. Read this file first.

## Project

- **Purpose:** MVP web app that turns an uploaded photo into a 3D model via the Tripo3D API (GLB download + STL conversion). The generation prompt in `main.py` is tuned for quadcopter drones.
- **Owner / data controller:** ASCENTIA s.r.o. (see `GDPR_COMPLIANCE.md`); maintained by Marián Stančík (GitHub `Abra7abra7`).
- **Hosting:** Render (`render.yaml`, Docker runtime, free plan, region Ohio/US). `GDPR_COMPLIANCE.md` lists moving to an EU region as an open item. TODO: confirm whether Render preview environments are enabled.

## Stack

- Python 3.11 (Docker image `python:3.11-slim`) · FastAPI · Uvicorn · httpx · trimesh/numpy · Jinja2
- Frontend: static HTML in `static/` (Slovak UI, `lang="sk"`) and `templates/index.html`
- Persistence: files in `output/` and `jobs.json` on local disk (both git-ignored); files older than `RETENTION_DAYS` (default 30) are deleted at startup.

## Commands

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000      # local dev (or: python main.py)
docker build -t tripo-mvp . && docker run -p 8000:8000 -e TRIPO_API_KEY=... tripo-mvp
curl http://localhost:8000/api/health      # smoke test
```

There is **no automated test suite and no linter config** in the repo. TODO: confirm whether to add `pytest` tests (e.g. for `/api/health` and upload validation).

## Structure

```
main.py               # FastAPI app: /, /privacy, /api/health, /api/upload, /api/job/{id}; background job pipeline
static/               # index.html, privacy.html (served by the app)
templates/index.html  # Jinja template
Dockerfile, render.yaml, requirements.txt
GDPR_COMPLIANCE.md, SCCS_TEMPLATE.md   # data-protection documentation
```

## Environment variables (names only)

- `TRIPO_API_KEY` (required, set in Render — never in git) · `RETENTION_DAYS` (optional, default 30) · `PORT` (set by Render)

## Project-specific rules

- Uploaded photos are personal data processed for ASCENTIA s.r.o.; keep the retention/auto-delete logic and `static/privacy.html` in sync with `GDPR_COMPLIANCE.md`.
- Every Tripo API call costs credits — do not run real generations in tests or CI without approval; mock the API.

### Working rules (mandatory for every agent: Jules, OpenCode, Hermes, Grok Bot, Claude, Codex, …)

- **Branch + Pull Request only.** Create a feature branch (`feat/…`, `fix/…`, `docs/…`, `seo/…`), open a PR and wait for review. **Never push or force-push to `main`/the default branch** and never merge your own PR.
- **No secrets in git.** Never commit `.env*`, API keys, tokens, passwords, private keys, server IP addresses, SSH details or personal data. Use the hosting platform's environment variables; reference variables by **name only**. If you find a secret in the repo, stop and report it — do not copy it anywhere.
- **GDPR / privacy first.** Treat any personal data (leads, customers, patients, form submissions) as confidential. No new trackers, cookies, analytics, third-party scripts or data processors without explicit approval; keep privacy/cookie pages consistent with what the code actually does.
- **The client owns the domain, the content and the data.** Do not change DNS, domains, hosting settings, payment settings, legal texts or published client content without explicit approval.
- **No destructive changes without approval.** No deleting pages/data/files in bulk, no history rewrites, no dependency major-version upgrades, no production deploys, no outgoing emails/posts from tests.
- **Invent nothing.** If a fact (price, company detail, legal statement, metric) is not in the repo or the task, leave a `TODO: confirm` instead of guessing.
- **Small, focused diffs.** Reuse existing patterns and dependencies; do not add a new dependency if an existing one covers the need.

### Definition of Done

1. All checks listed under *Commands* that exist for this repo pass locally (build, tests, lint/verification).
2. The **preview deploy** of the PR branch was opened and checked (desktop + mobile) — or, if this repo has no preview, the reason is stated in the PR.
3. The PR description contains: a short summary of *what* and *why*, the list of changed areas, how it was tested, the preview URL, and any `TODO: confirm` items or risks.
4. Nothing goes live until Marián approves (**ÁNO**) and merges the PR.
