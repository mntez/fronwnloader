import os
import shutil
from pathlib import Path


def get_ffmpeg_location() -> str | None:
    """Return an explicit FFmpeg location or resolve it from PATH."""
    configured = os.getenv("FFMPEG_LOCATION", "").strip().strip('"')
    if configured:
        location = Path(configured).expanduser()
        if location.is_dir():
            executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
            return str(location) if (location / executable).is_file() else None
        if location.is_file() and location.name.lower() in {"ffmpeg", "ffmpeg.exe"}:
            return str(location)
        return None
    return shutil.which("ffmpeg")
