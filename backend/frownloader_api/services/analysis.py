import ipaddress
import os
import socket
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from urllib.parse import urlsplit

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from frownloader_api.media_tools import get_ffmpeg_location


SUPPORTED_HOSTS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "youtube-nocookie.com": "YouTube",
    "facebook.com": "Facebook",
    "fb.watch": "Facebook",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "discord.com": "Discord",
    "discordapp.com": "Discord",
    "discordapp.net": "Discord",
    "pinterest.com": "Pinterest",
    "pin.it": "Pinterest",
    "reddit.com": "Reddit",
    "redd.it": "Reddit",
    "threads.net": "Threads",
    "x.com": "X",
    "twitter.com": "X",
    "t.co": "X",
}


class AnalysisError(Exception):
    """A safe, user-facing error raised while analyzing a video URL."""


_VALIDATED_FORMAT_TTL_SECONDS = 180
_MAX_VALIDATED_FORMATS = 512
_validated_formats_lock = threading.Lock()
_validated_formats: dict[tuple[str, str], tuple[float, dict]] = {}


def _thumbnail_url(info: dict) -> str | None:
    """Choose the most useful direct thumbnail URL from extractor metadata."""
    thumbnails = info.get("thumbnails") or []
    candidates = [item for item in thumbnails if isinstance(item, dict) and item.get("url")]
    if candidates:
        # Prefer larger thumbnails while retaining extractor ordering as a tie-breaker.
        best = max(
            enumerate(candidates),
            key=lambda pair: (
                (pair[1].get("width") or 0) * (pair[1].get("height") or 0),
                pair[1].get("preference") or 0,
                pair[0],
            ),
        )[1]
        return best["url"]
    thumbnail = info.get("thumbnail")
    return thumbnail if isinstance(thumbnail, str) and thumbnail.startswith(("https://", "http://")) else None


class _ValidatedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        _validate_public_http_url(new_url)
        return super().redirect_request(request, response, code, message, headers, new_url)


def _platform_for_host(host: str) -> str | None:
    normalized = host.lower().rstrip(".")
    for domain, platform in SUPPORTED_HOSTS.items():
        if normalized == domain or normalized.endswith(f".{domain}"):
            return platform
    return None


def _parse_http_url(raw_url: str):
    try:
        parsed = urlsplit(raw_url.strip())
        host = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
            raise AnalysisError("Enter a valid public video URL using HTTP or HTTPS.")
        if parsed.port not in {None, 80, 443}:
            raise AnalysisError("Video URLs using custom ports are not supported.")
    except ValueError as exc:
        raise AnalysisError("Enter a valid public video URL using HTTP or HTTPS.") from exc
    return parsed, host


def _validate_public_http_url(raw_url: str) -> None:
    parsed, host = _parse_http_url(raw_url)
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except OSError as exc:
        raise AnalysisError("The video destination could not be safely verified. Check the link and try again.") from exc

    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise AnalysisError("Private or local network addresses are not allowed.")


def validate_video_url(raw_url: str) -> tuple[str, str]:
    parsed, host = _parse_http_url(raw_url)
    platform = _platform_for_host(host)
    if platform is None:
        raise AnalysisError("This video platform is not supported. Try YouTube, Facebook, Instagram, TikTok, Discord, Pinterest, Reddit, Threads, or X.")

    _validate_public_http_url(parsed.geturl())

    # Inspect the redirect chain before yt-dlp follows it. A ranged GET is more
    # widely supported than HEAD and closes without reading media into memory.
    try:
        request = Request(
            parsed.geturl(),
            headers={
                "Range": "bytes=0-0",
                "User-Agent": "Mozilla/5.0 (compatible; Frownloader/1.0)",
            },
        )
        # The preflight must verify destination DNS and connect to that host
        # directly. Inherited HTTP(S)_PROXY settings can otherwise send the
        # request to an unrelated or unavailable proxy before validation runs.
        opener = build_opener(ProxyHandler({}), _ValidatedRedirectHandler())
        with opener.open(request, timeout=6) as response:
            _validate_public_http_url(response.geturl())
    except HTTPError as exc:
        try:
            _validate_public_http_url(exc.geturl())
        finally:
            exc.close()
    except AnalysisError:
        raise
    except (OSError, URLError, TimeoutError) as exc:
        raise AnalysisError("The video destination could not be safely verified. Check the link and try again.") from exc

    return parsed.geturl(), platform


def _available_formats(info: dict) -> list[dict]:
    formats: dict[tuple[str, str], dict] = {}
    seen_format_ids: set[str] = set()
    for item in info.get("formats") or []:
        format_id = item.get("format_id")
        if not format_id or format_id in seen_format_ids:
            continue
        seen_format_ids.add(format_id)

        has_video = item.get("vcodec") not in {None, "none"}
        has_audio = item.get("acodec") not in {None, "none"}
        if not has_video and not has_audio:
            continue

        height = item.get("height") if has_video else None
        ext = item.get("ext")
        kind = "video" if has_video else "audio"
        key = (kind, f"{height or 0}:{ext or ''}")
        if key in formats:
            previous = formats[key]
            previous_size = previous.get("filesize") or previous.get("filesize_approx") or 0
            current_size = item.get("filesize") or item.get("filesize_approx") or 0
            if previous_size >= current_size:
                continue

        exact_size = item.get("filesize")
        approximate_size = item.get("filesize_approx")
        formats[key] = {
            "format_id": format_id,
            "kind": kind,
            "height": height,
            "ext": ext,
            "has_audio": has_audio,
            "filesize": exact_size if exact_size is not None else approximate_size,
            "filesize_is_approx": exact_size is None and approximate_size is not None,
        }

    result = sorted(
        formats.values(),
        key=lambda item: (item["kind"] != "video", -(item["height"] or 0), item["ext"] or ""),
    )
    has_source_audio = any(item.get("acodec") not in {None, "none"} for item in info.get("formats") or [])
    available = []
    for item in result:
        outputs = _output_formats(item, has_source_audio)
        if outputs:
            available.append({**item, "output_formats": outputs})
    return available


def _output_formats(source_format: dict, has_source_audio: bool) -> list[dict[str, str]]:
    kind = source_format["kind"]
    ext = source_format.get("ext")
    can_merge = get_ffmpeg_location() is not None
    output_formats: list[dict[str, str]] = []

    if kind == "audio":
        output_formats.append({"id": "source", "label": f"Original audio{f' ({ext.upper()})' if ext else ''}"})
        if can_merge and ext != "mp3":
            output_formats.append({"id": "mp3", "label": "MP3 audio"})
        return output_formats

    if source_format.get("has_audio") or can_merge:
        if source_format.get("has_audio"):
            source_label = f"Original video{f' ({ext.upper()})' if ext else ''}"
        else:
            source_label = "MKV video (merged with source audio)"
        output_formats.append({"id": "source", "label": source_label})
    if can_merge and (ext != "mp4" or not source_format.get("has_audio")):
        output_formats.append({"id": "mp4", "label": "MP4 video"})
    if can_merge and has_source_audio:
        output_formats.append({"id": "mp3", "label": "MP3 audio"})
    return output_formats


def analyze_video(raw_url: str) -> dict:
    url, platform = validate_video_url(raw_url)
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 15,
        # Ignore inherited system proxies by default; they may be unavailable
        # and would prevent requests to the preflight-verified public host.
        "proxy": os.getenv("YTDLP_PROXY", ""),
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as exc:
        raise AnalysisError("Could not analyze this video. It may be private, unavailable, or restricted by the platform.") from exc
    except Exception as exc:
        raise AnalysisError("The video could not be analyzed right now. Please try again.") from exc

    if not isinstance(info, dict):
        raise AnalysisError("The platform did not return video information for this link.")

    return {
        "title": info.get("title") or "Untitled video",
        "thumbnail": _thumbnail_url(info),
        "duration": info.get("duration"),
        "platform": platform,
        "formats": _available_formats(info),
    }


def validate_format_selection(raw_url: str, format_id: str, output_format: str | None = None) -> dict:
    """Confirm a submitted format id belongs to the currently analyzed video."""
    key = (raw_url.strip(), format_id)
    now = time.monotonic()
    with _validated_formats_lock:
        cached = _validated_formats.get(key)
        if cached and now - cached[0] < _VALIDATED_FORMAT_TTL_SECONDS:
            result = dict(cached[1])
            if output_format is not None and output_format not in {
                item["id"] for item in result["output_formats"]
            }:
                raise AnalysisError("That output format is not available for the selected source format.")
            return result
        if cached:
            _validated_formats.pop(key, None)

    analysis = analyze_video(raw_url)
    selected = next(
        (item for item in analysis["formats"] if item["format_id"] == format_id),
        None,
    )
    if selected is None:
        raise AnalysisError("That format is no longer available. Analyze the link again and choose a listed format.")
    result = {**selected, "duration": analysis["duration"]}
    if output_format is not None and output_format not in {
        item["id"] for item in result["output_formats"]
    }:
        raise AnalysisError("That output format is not available for the selected source format.")

    with _validated_formats_lock:
        expired = [
            cached_key for cached_key, (created_at, _) in _validated_formats.items()
            if now - created_at >= _VALIDATED_FORMAT_TTL_SECONDS
        ]
        for cached_key in expired:
            _validated_formats.pop(cached_key, None)
        if len(_validated_formats) >= _MAX_VALIDATED_FORMATS:
            oldest_key = min(_validated_formats, key=lambda cached_key: _validated_formats[cached_key][0])
            _validated_formats.pop(oldest_key, None)
        _validated_formats[key] = (now, dict(result))
    return result
