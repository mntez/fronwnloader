import asyncio
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from frownloader_api.services.analysis import AnalysisError, analyze_video, validate_format_selection
from frownloader_api.services.jobs import (
    cleanup_loop,
    create_download_job,
    get_completed_file,
    get_job,
    release_file_stream,
    shutdown_executor,
)
from frownloader_api.media_tools import get_ffmpeg_location


def _allowed_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


RATE_LIMIT_REQUESTS = max(1, int(os.getenv("API_RATE_LIMIT_REQUESTS", "20")))
RATE_LIMIT_WINDOW_SECONDS = max(10, int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60")))
_rate_limit_lock = threading.Lock()
_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(request: Request) -> None:
    client_key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_limit_lock:
        bucket = _rate_limit_buckets[client_key]
        while bucket and now - bucket[0] >= RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(_rate_limit_buckets) > 10_000:
            for key, values in list(_rate_limit_buckets.items()):
                if key != client_key and (not values or now - values[-1] >= RATE_LIMIT_WINDOW_SECONDS):
                    _rate_limit_buckets.pop(key, None)
        if client_key not in _rate_limit_buckets and len(_rate_limit_buckets) >= 15_000:
            raise HTTPException(status_code=429, detail="The service is busy. Please try again shortly.")
        if len(bucket) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment and try again.")
        bucket.append(now)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    cleanup_task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        shutdown_executor()


app = FastAPI(title="Frownloader API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


class FormatSelectionRequest(AnalyzeRequest):
    format_id: str = Field(min_length=1, max_length=100)
    output_format: str = Field(default="source", min_length=1, max_length=20)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str | bool]:
    return {"status": "ok", "ffmpeg_available": get_ffmpeg_location() is not None}


@app.post("/api/analyze", tags=["analysis"])
async def analyze(request: AnalyzeRequest, http_request: Request) -> dict:
    _check_rate_limit(http_request)
    try:
        return await run_in_threadpool(analyze_video, request.url)
    except AnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/formats/validate", tags=["formats"])
async def validate_format(request: FormatSelectionRequest, http_request: Request) -> dict:
    _check_rate_limit(http_request)
    try:
        selected = await run_in_threadpool(
            validate_format_selection,
            request.url,
            request.format_id,
            request.output_format,
        )
        return {"format": selected}
    except AnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/downloads", tags=["downloads"])
async def start_download(request: FormatSelectionRequest, http_request: Request) -> dict:
    _check_rate_limit(http_request)
    try:
        return await run_in_threadpool(
            create_download_job,
            request.url,
            request.format_id,
            request.output_format,
        )
    except AnalysisError as exc:
        status_code = 429 if "busy" in str(exc).lower() else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Temporary download storage is unavailable.") from exc


@app.get("/api/downloads/{job_id}", tags=["downloads"])
async def download_status(job_id: str) -> dict:
    if len(job_id) != 32 or any(character not in "0123456789abcdef" for character in job_id):
        raise HTTPException(status_code=404, detail="Download job not found.")
    result = await run_in_threadpool(get_job, job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Download job not found or expired.")
    return result


@app.get("/api/downloads/{job_id}/file", tags=["downloads"])
async def download_file(job_id: str) -> FileResponse:
    if len(job_id) != 32 or any(character not in "0123456789abcdef" for character in job_id):
        raise HTTPException(status_code=404, detail="Download job not found.")
    result = await run_in_threadpool(get_completed_file, job_id)
    if result is None:
        status = await run_in_threadpool(get_job, job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Download job not found or expired.")
        if status["status"] != "complete":
            raise HTTPException(status_code=409, detail="The download is not ready yet.")
        raise HTTPException(status_code=404, detail="The completed file is no longer available.")
    file_path, filename = result
    return FileResponse(
        path=Path(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(release_file_stream, job_id),
    )
