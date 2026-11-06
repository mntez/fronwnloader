import asyncio
import hashlib
import os
import shutil
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from frownloader_api.media_tools import get_ffmpeg_location
from frownloader_api.services.analysis import AnalysisError, validate_format_selection, validate_video_url


MAX_CONCURRENT_DOWNLOADS = max(1, int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2")))
MAX_DOWNLOAD_BYTES = max(1, int(os.getenv("MAX_DOWNLOAD_BYTES", str(1024**3))))
MAX_VIDEO_DURATION = max(60, int(os.getenv("MAX_VIDEO_DURATION_SECONDS", str(2 * 60 * 60))))
MAX_DOWNLOAD_SECONDS = max(60, int(os.getenv("MAX_DOWNLOAD_SECONDS", str(30 * 60))))
JOB_TTL_SECONDS = max(60, int(os.getenv("JOB_TTL_SECONDS", str(60 * 60))))
CLEANUP_INTERVAL_SECONDS = max(30, int(os.getenv("JOB_CLEANUP_INTERVAL_SECONDS", "60")))
TEMP_ROOT = Path(os.getenv("FROWNLOADER_TEMP_DIR", Path(tempfile.gettempdir()) / "frownloader-jobs")).resolve()


@dataclass
class DownloadJob:
    job_id: str
    fingerprint: str
    status: str = "queued"
    progress: float | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    filename: str | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    job_dir: Path | None = None
    file_path: Path | None = None
    active_streams: int = 0


_jobs: dict[str, DownloadJob] = {}
_active_fingerprints: dict[str, str] = {}
_lock = threading.RLock()
_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS, thread_name_prefix="frownloader-download")


def _fingerprint(url: str, format_id: str, output_format: str) -> str:
    return hashlib.sha256(f"{url}\0{format_id}\0{output_format}".encode("utf-8")).hexdigest()


def _snapshot(job: DownloadJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "downloaded_bytes": job.downloaded_bytes,
        "total_bytes": job.total_bytes,
        "filename": job.filename if job.status == "complete" else None,
        "error": job.error,
    }


def create_download_job(url: str, format_id: str, output_format: str = "source") -> dict[str, Any]:
    cleanup_expired_jobs()
    normalized_url, _ = validate_video_url(url)
    selected = validate_format_selection(normalized_url, format_id, output_format)
    fingerprint = _fingerprint(normalized_url, format_id, output_format)

    with _lock:
        existing_id = _active_fingerprints.get(fingerprint)
        if existing_id:
            existing = _jobs.get(existing_id)
            if existing and existing.status in {"queued", "downloading", "complete"}:
                return _snapshot(existing)
            _active_fingerprints.pop(fingerprint, None)

        active_count = sum(job.status in {"queued", "downloading"} for job in _jobs.values())
        if active_count >= MAX_CONCURRENT_DOWNLOADS:
            raise AnalysisError("The downloader is busy. Please try again in a moment.")

        job_id = uuid.uuid4().hex
        job_dir = (TEMP_ROOT / job_id).resolve()
        if TEMP_ROOT not in job_dir.parents:
            raise AnalysisError("Could not create a temporary download job.")
        job_dir.mkdir(parents=True, exist_ok=False)

        job = DownloadJob(job_id=job_id, fingerprint=fingerprint, job_dir=job_dir)
        _jobs[job_id] = job
        _active_fingerprints[fingerprint] = job_id

    _executor.submit(_run_download, job_id, normalized_url, selected, output_format)
    return _snapshot(job)


def _run_download(job_id: str, url: str, selected: dict[str, Any], output_format: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job.job_dir is None:
            return
        job.status = "downloading"
        job_dir = job.job_dir

    duration = selected.get("duration")
    if duration is not None and duration > MAX_VIDEO_DURATION:
        _fail_job(job_id, "This video exceeds the configured maximum duration.")
        return

    selected_id = selected["format_id"]
    selected_has_video = selected["kind"] == "video"
    if output_format == "mp3":
        format_selector = "bestaudio"
    elif selected_has_video and not selected["has_audio"]:
        format_selector = f"{selected_id}+bestaudio"
    else:
        format_selector = selected_id

    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": format_selector,
        "outtmpl": str(job_dir / "media.%(ext)s"),
        "restrictfilenames": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
        "max_filesize": MAX_DOWNLOAD_BYTES,
        "proxy": os.getenv("YTDLP_PROXY", ""),
    }
    ffmpeg_location = get_ffmpeg_location()
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    if output_format == "mp3":
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif output_format == "mp4":
        options["merge_output_format"] = "mp4"
        options["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    elif selected_has_video and not selected["has_audio"]:
        options["merge_output_format"] = "mkv"

    started_at = time.monotonic()
    options["progress_hooks"] = [lambda data: _progress_hook(job_id, data, started_at)]

    try:
        # create_download_job validates the URL before enqueueing. Repeating
        # the external redirect/DNS preflight here adds another failure point
        # after the user has already received a queued job.
        with YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [path for path in job_dir.iterdir() if path.is_file() and not path.name.endswith(".part")]
        if len(files) != 1:
            raise DownloadError("The downloader did not produce a single completed output file.")

        result_path = files[0].resolve()
        if job_dir not in result_path.parents or result_path.stat().st_size > MAX_DOWNLOAD_BYTES:
            raise DownloadError("The downloaded file exceeded the allowed limit.")

        with _lock:
            current = _jobs.get(job_id)
            if current is None:
                shutil.rmtree(job_dir, ignore_errors=True)
                return
            current.status = "complete"
            current.progress = 100.0
            current.downloaded_bytes = result_path.stat().st_size
            current.total_bytes = result_path.stat().st_size
            current.filename = result_path.name
            current.file_path = result_path
            current.completed_at = time.time()
    except Exception as exc:
        _fail_job(job_id, _safe_download_error(exc))


def _safe_download_error(error: Exception) -> str:
    """Map extractor errors to useful messages without returning raw URLs or tokens."""
    message = str(error).lower()
    if "maximum file size" in message or "filesize" in message:
        return "This download exceeds the configured file size limit."
    if "ffmpeg" in message:
        return "FFmpeg could not process this video. Check that FFmpeg is available and try again."
    if "requested format" in message or "format is not available" in message:
        return "The selected quality is no longer available. Analyze the link again and choose another format."
    if "403" in message or "forbidden" in message or "429" in message or "too many requests" in message:
        return "The platform temporarily blocked this request. Wait a while and try again."
    if "timed out" in message or "timeout" in message or "connection" in message:
        return "The connection to the video platform timed out. Check your connection and try again."
    if "private" in message or "login" in message or "sign in" in message:
        return "This video may be private or require a platform login. Only public videos can be downloaded."
    if isinstance(error, DownloadError):
        return "The platform could not provide this video in the selected format. Try another available format."
    return "The download failed. The video may be unavailable or restricted by the platform."


def _progress_hook(job_id: str, data: dict[str, Any], started_at: float) -> None:
    if time.monotonic() - started_at > MAX_DOWNLOAD_SECONDS:
        raise DownloadError("Download exceeded maximum time limit")
    status = data.get("status")
    downloaded = int(data.get("downloaded_bytes") or 0)
    total = data.get("total_bytes") or data.get("total_bytes_estimate")
    total = int(total) if total else None
    if downloaded > MAX_DOWNLOAD_BYTES or (total is not None and total > MAX_DOWNLOAD_BYTES):
        raise DownloadError("Download exceeded maximum file size")

    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            raise DownloadError("Download job expired")
        job.status = "downloading"
        job.downloaded_bytes = downloaded
        job.total_bytes = total
        job.progress = min(99.9, downloaded * 100 / total) if total else None


def _fail_job(job_id: str, message: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job.status = "failed"
        job.error = message
        job.completed_at = time.time()
        job.file_path = None
        job.filename = None
        job_dir = job.job_dir
    if job_dir:
        shutil.rmtree(job_dir, ignore_errors=True)


def get_job(job_id: str) -> dict[str, Any] | None:
    cleanup_expired_jobs()
    with _lock:
        job = _jobs.get(job_id)
        return _snapshot(job) if job else None


def get_completed_file(job_id: str) -> tuple[Path, str] | None:
    cleanup_expired_jobs()
    with _lock:
        job = _jobs.get(job_id)
        if job is None or job.status != "complete" or job.file_path is None or job.filename is None:
            return None
        path = job.file_path.resolve()
        if job.job_dir is None or job.job_dir.resolve() not in path.parents or not path.is_file():
            return None
        job.active_streams += 1
        return path, job.filename


def release_file_stream(job_id: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.active_streams = max(0, job.active_streams - 1)


def cleanup_expired_jobs(now: float | None = None) -> int:
    current_time = now if now is not None else time.time()
    expired: list[DownloadJob] = []
    with _lock:
        for job_id, job in list(_jobs.items()):
            expiry_base = job.completed_at or job.created_at
            if job.status in {"queued", "downloading"} or job.active_streams or current_time - expiry_base < JOB_TTL_SECONDS:
                continue
            expired.append(_jobs.pop(job_id))
            if _active_fingerprints.get(job.fingerprint) == job_id:
                _active_fingerprints.pop(job.fingerprint, None)

    for job in expired:
        if job.job_dir:
            shutil.rmtree(job.job_dir, ignore_errors=True)

    with _lock:
        active_dirs = {
            job.job_dir
            for job in _jobs.values()
            if job.status in {"queued", "downloading"} or job.active_streams
        }
    if TEMP_ROOT.exists():
        for path in TEMP_ROOT.iterdir():
            try:
                resolved = path.resolve()
                if path.is_dir() and resolved not in active_dirs and current_time - path.stat().st_mtime >= JOB_TTL_SECONDS:
                    shutil.rmtree(path, ignore_errors=True)
            except OSError:
                continue
    return len(expired)


async def cleanup_loop() -> None:
    while True:
        await asyncio.to_thread(cleanup_expired_jobs)
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


def shutdown_executor() -> None:
    _executor.shutdown(wait=False, cancel_futures=True)
