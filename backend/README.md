# Frownloader API

## Local development

From this directory, create and activate a Python virtual environment, install
the requirements, then start the API:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn frownloader_api.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

The health endpoint is available at `http://127.0.0.1:8000/health`.
Set values in `.env` (see `.env.example`), including the exact allowed frontend
origins and the download limits. The API uses at most two concurrent download
workers by default, caps videos at two hours and downloads at 30 minutes/1 GiB,
limits analysis, format validation, and job-creation requests to 20 per minute
per client, and retains completed files for one hour. Adjust these values for
your server.

The frontend sends `POST /api/analyze` with a JSON body containing `url`. It
returns video title, thumbnail, duration, platform, and formats reported by
yt-dlp. Set the frontend's `NEXT_PUBLIC_API_URL` (see
`../frontend/.env.example`) if the API is running at a different address.

Analysis accepts public links from YouTube, Facebook, Instagram, TikTok,
Discord, Pinterest, Reddit, Threads, and X. yt-dlp has dedicated extractors for
some platforms and uses generic video detection for others; availability varies
by link, privacy, login requirements, and platform changes. Only formats
returned for a specific video are listed.

The API permits only HTTP(S) links on the supported platforms, rejects private
or local resolved addresses, and checks redirect targets before yt-dlp runs.
Preflight fails closed if it cannot verify the destination.

The format selector lists the source formats returned for that video. When
FFmpeg is available, it also offers MP4 video and MP3 audio conversion where
applicable; these choices are validated against the selected source type.

The format picker submits the selected yt-dlp format ID to
`POST /api/formats/validate`. The API re-extracts the source and confirms that
the requested format is still present before acknowledging the selection.

## Download jobs

- `POST /api/downloads` with `url` and `format_id` creates or returns the active
  matching job.
- `GET /api/downloads/{job_id}` returns the real yt-dlp state and progress.
- `GET /api/downloads/{job_id}/file` streams a completed file to the browser.
- Job IDs are random and job state is kept in memory. Temporary media lives
  outside the repository, is removed on failure, and expires after
  `JOB_TTL_SECONDS`. Cleanup skips active transfers and downloads.

Install FFmpeg and ensure `ffmpeg` is on `PATH` (`ffmpeg -version` should print
its version). yt-dlp uses it to merge separate video and audio streams. Run a
single API process for this in-memory job registry; multiple workers would not
share job state.

## Verify locally

Check the API and FFmpeg detection:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Analyze a public link you are authorized to download:

```powershell
$body = @{ url = "https://www.youtube.com/watch?v=REPLACE_WITH_VIDEO_ID" } | ConvertTo-Json
$video = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/analyze -ContentType "application/json" -Body $body
$video | ConvertTo-Json -Depth 8
```

Choose a returned `format_id` and, if desired, one of its `output_formats` IDs
to call `POST /api/downloads`. Poll `GET /api/downloads/{job_id}` until the
status is `complete` or `failed`; only then request the `/file` endpoint. Test
invalid links separately and confirm they return a readable 4xx response.
