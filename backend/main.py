from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from uuid import uuid4
from pathlib import Path
import json, shutil
from ap_analyzer.analysis.action_potential import ActionPotentialProcessor
from ap_analyzer.io_utils.io_utils import ATFHandler

DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True, parents=True)
app = FastAPI(title="AP-Analyzer API")

@app.post("/analyze")
async def analyze(file: UploadFile, bg: BackgroundTasks):
    task_id = uuid4().hex
    infile  = DATA_DIR / f"{task_id}.atf"
    infile.write_bytes(await file.read())
    bg.add_task(run_analysis, infile, task_id)
    return {"task_id": task_id, "status": "PENDING"}

@app.get("/result/{task_id}")
def result(task_id: str):
    meta = DATA_DIR / f"{task_id}.json"
    if not meta.exists():
        raise HTTPException(404)
    return json.loads(meta.read_text())

def run_analysis(path: Path, task_id: str):
    try:
        h = ATFHandler(str(path))
        h.load_atf()
        proc = ActionPotentialProcessor()
        proc.set_data(h.get_column("#1"), h.get_column("Time"))
        res = proc.analyze()
        (DATA_DIR / f"{task_id}.json").write_text(json.dumps(res, default=str))
    except Exception as exc:
        (DATA_DIR / f"{task_id}.json").write_text(json.dumps({"error": str(exc)}))
