"""Aplicação FastAPI que orquestra jobs de audiodescrição.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from adtool.config import AppConfig
from adtool.pipeline.core import ADPipeline

app = FastAPI(title="Audiodescrição Toolkit API", version="0.1.0")
_jobs: Dict[str, dict] = {}


class JobCreate(BaseModel):
    url: str | None = None


class JobStatus(BaseModel):
    id: str
    status: str
    progress: float
    assets: list[str]


def get_outputs(job_id: str) -> Path:
    base = Path("/app/outputs")
    base.mkdir(parents=True, exist_ok=True)
    return base / job_id


@app.post("/jobs", response_model=JobStatus)
async def create_job(url: str | None = None, file: UploadFile | None = File(default=None)) -> JobStatus:
    job_id = uuid.uuid4().hex
    output_dir = get_outputs(job_id)
    pipeline = ADPipeline(AppConfig(work_dir=output_dir))
    if file:
        content = await file.read()
        media_path = output_dir / file.filename
        output_dir.mkdir(parents=True, exist_ok=True)
        media_path.write_bytes(content)
        input_path = str(media_path)
    elif url:
        input_path = url
    else:
        raise HTTPException(status_code=400, detail="Informe arquivo ou URL")

    artifacts = pipeline.run(input_path, output_dir, export_video=True)
    assets = [
        str(artifacts.script_srt),
        str(artifacts.script_txt),
        str(artifacts.tts_wav),
        str(artifacts.tts_mp3),
    ]
    if artifacts.final_video:
        assets.append(str(artifacts.final_video))
    status = JobStatus(id=job_id, status="done", progress=1.0, assets=assets)
    _jobs[job_id] = status.model_dump()
    return status


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def job_status(job_id: str) -> JobStatus:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return JobStatus.model_validate(_jobs[job_id])


@app.get("/jobs/{job_id}/download")
async def download_asset(job_id: str, path: str) -> FileResponse:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path)
