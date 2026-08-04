import os, uuid, asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx

# ── Config ──
TRIPO_API_KEY = os.environ.get("TRIPO_API_KEY", "")
if not TRIPO_API_KEY:
    raise RuntimeError("TRIPO_API_KEY env var required")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Tripo3D MVP")

# Serve static and output files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# In-memory job store
jobs: dict[str, dict] = {}

TRIPO_HEADERS = {"Authorization": f"Bearer {TRIPO_API_KEY}"}

async def process_job(job_id: str, image_bytes: bytes, filename: str):
    """Background task: upload → generate → poll → download → convert"""
    jobs[job_id] = {"status": "uploading", "progress": 10, "job_id": job_id}
    try:
        # 1. Upload to Tripo
        async with httpx.AsyncClient(timeout=30) as client:
            jobs[job_id]["status"] = "uploading"
            jobs[job_id]["progress"] = 15
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
        jobs[job_id]["status"] = "generating"
        jobs[job_id]["progress"] = 30
        async with httpx.AsyncClient(timeout=30) as client:
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
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 50
        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(60):
                resp = await client.get(
                    f"https://openapi.tripo3d.ai/v3/tasks/{task_id}",
                    headers=TRIPO_HEADERS
                )
                d = resp.json()["data"]
                jobs[job_id]["progress"] = min(50 + int(d.get("progress", 0) * 0.3), 80)
                if d["status"] == "success":
                    output = d["output"]
                    break
                elif d["status"] in ("failed", "cancelled"):
                    raise Exception(f"Task failed: {d}")
                await asyncio.sleep(5)
            else:
                raise Exception("Task timed out")

        # 4. Download
        jobs[job_id]["status"] = "downloading"
        jobs[job_id]["progress"] = 82
        async with httpx.AsyncClient(timeout=120) as client:
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
        jobs[job_id]["status"] = "exporting"
        jobs[job_id]["progress"] = 90
        try:
            import trimesh
            scene = trimesh.load(str(glb_path))
            mesh = list(scene.geometry.values())[0] if isinstance(scene, trimesh.Scene) else scene
            stl_path = OUTPUT_DIR / f"{job_id}.stl"
            mesh.export(str(stl_path), file_type="stl")
            has_stl = True
        except Exception as e:
            has_stl = False

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "glb": f"/output/{job_id}.glb",
            "stl": f"/output/{job_id}.stl" if has_stl else None,
        })

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

# ── Routes ──

@app.get("/", response_class=HTMLResponse)
async def index():
    index_html = (BASE_DIR / "static" / "index.html").read_text()
    return HTMLResponse(index_html)

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