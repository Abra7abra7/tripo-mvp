import os, uuid, asyncio, json, time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

# ── Config ──
TRIPO_API_KEY = os.environ.get("TRIPO_API_KEY", "")
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

JOBS_FILE = BASE_DIR / "jobs.json"
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", 30))

# ── Persistent job store ──
def _load_jobs() -> dict[str, dict]:
    if JOBS_FILE.exists():
        try:
            data = json.loads(JOBS_FILE.read_text())
            return {k: v for k, v in data.items() if v.get("status") not in ("done", "error")}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def _save_jobs():
    try:
        JOBS_FILE.write_text(json.dumps(jobs, indent=2))
    except OSError:
        pass  # non-critical write, best effort

jobs: dict[str, dict] = _load_jobs()

app = FastAPI(title="Tripo3D MVP")

# Auto-delete old files on startup
@app.on_event("startup")
async def cleanup_old_files():
    """Delete files and jobs older than RETENTION_DAYS"""
    cutoff = time.time() - (RETENTION_DAYS * 86400)
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
    # Prune orphaned jobs from JSON (no corresponding file on disk)
    if JOBS_FILE.exists():
        try:
            data = json.loads(JOBS_FILE.read_text())
            active_job_ids = {p.stem for p in OUTPUT_DIR.iterdir() if p.suffix in ('.glb', '.stl')}
            data = {k: v for k, v in data.items() if k in active_job_ids}
            JOBS_FILE.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, OSError):
            pass

# Serve static and output files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

TRIPO_HEADERS = {"Authorization": f"Bearer {TRIPO_API_KEY}"}

# ── Helpers ──
def _set_job(job_id: str, **updates):
    job = jobs.get(job_id)
    if job:
        job.update(updates)
    _save_jobs()

async def process_job(job_id: str, image_bytes: bytes, filename: str):
    """Background task: upload → generate → poll → download → convert"""
    jobs[job_id] = {"status": "uploading", "progress": 10, "job_id": job_id}
    _save_jobs()
    try:
        # 1. Upload to Tripo
        async with httpx.AsyncClient(timeout=60) as client:
            _set_job(job_id, status="uploading", progress=15)
            resp = await client.post(
                "https://api.tripo3d.ai/v2/openapi/upload/sts",
                headers=TRIPO_HEADERS,
                files={"file": (filename, image_bytes, "image/jpeg")}
            )
            data = resp.json()
            if data.get("code") != 0:
                raise Exception(f"Upload failed: {data}")
            file_token = data["data"]["image_token"]

        # 2. Generate
        _set_job(job_id, status="generating", progress=30)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openapi.tripo3d.ai/v3/generation/image-to-model",
                headers=TRIPO_HEADERS,
                json={
                    "file": {"file_token": file_token, "type": "jpeg"},
                    "prompt": "quadcopter drone, detailed 3D model, accurate geometry",
                    "model": "v3.1-20260211",
                    "texture": True,
                    "pbr": True
                }
            )
            data = resp.json()
            if data.get("code") != 0:
                raise Exception(f"Generation failed: {data}")
            task_id = data["data"]["task_id"]

        # 3. Poll
        _set_job(job_id, status="processing", progress=50)
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(60):
                resp = await client.get(
                    f"https://openapi.tripo3d.ai/v3/tasks/{task_id}",
                    headers=TRIPO_HEADERS
                )
                d = resp.json()["data"]
                progress = min(50 + int(d.get("progress", 0) * 0.3), 80)
                _set_job(job_id, progress=progress)
                if d["status"] == "success":
                    output = d["output"]
                    break
                elif d["status"] in ("failed", "cancelled"):
                    raise Exception(f"Task failed: {d}")
                await asyncio.sleep(5)
            else:
                raise Exception("Task timed out")

        # 4. Download from Tripo
        _set_job(job_id, status="downloading", progress=82)
        async with httpx.AsyncClient(timeout=300) as client:  # longer timeout for large files
            resp = await client.get(output["model_url"])
            glb_path = OUTPUT_DIR / f"{job_id}.glb"
            with open(glb_path, "wb") as f:
                f.write(resp.content)

            if output.get("rendered_image_url"):
                resp_r = await client.get(output["rendered_image_url"])
                rnd_path = OUTPUT_DIR / f"{job_id}_render.webp"
                with open(rnd_path, "wb") as f:
                    f.write(resp_r.content)

        # 5. Convert to STL
        _set_job(job_id, status="exporting", progress=90)
        try:
            import trimesh
            scene = trimesh.load(str(glb_path))
            mesh = list(scene.geometry.values())[0] if isinstance(scene, trimesh.Scene) else scene
            stl_path = OUTPUT_DIR / f"{job_id}.stl"
            mesh.export(str(stl_path), file_type="stl")
            has_stl = True
        except Exception:
            has_stl = False

        _set_job(job_id,
            status="done",
            progress=100,
            glb=f"/output/{job_id}.glb",
            stl=f"/output/{job_id}.stl" if has_stl else None,
        )

    except Exception as e:
        _set_job(job_id, status="error", error=str(e))

# ── Routes ──

@app.get("/", response_class=HTMLResponse)
async def index():
    index_html = (BASE_DIR / "static" / "index.html").read_text()
    return HTMLResponse(index_html)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    privacy_html = (BASE_DIR / "static" / "privacy.html").read_text()
    return HTMLResponse(privacy_html)

@app.get("/api/health")
async def health():
    key_ok = bool(TRIPO_API_KEY)
    return JSONResponse({"status": "ok", "tripo_api_key_configured": key_ok})

@app.post("/api/upload")
async def upload_and_generate(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename or not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(400, "Only JPG, PNG, WebP images supported")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 20 MB)")

    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(process_job, job_id, image_bytes, file.filename)

    return JSONResponse({"job_id": job_id, "status": "queued"})

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JSONResponse(job)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)