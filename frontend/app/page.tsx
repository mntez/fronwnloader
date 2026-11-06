"use client";

import { useRef, useState, type ClipboardEvent, type FormEvent } from "react";
import Policies from "./policies";
import { siteConfig } from "../lib/site-config";

type VideoFormat = {
  format_id: string | null;
  kind: "video" | "audio";
  height: number | null;
  ext: string | null;
  has_audio: boolean;
  filesize: number | null;
  filesize_is_approx: boolean;
  output_formats: OutputFormat[];
};

type OutputFormat = { id: string; label: string };

type VideoAnalysis = {
  title: string;
  thumbnail: string | null;
  duration: number | null;
  platform: string;
  formats: VideoFormat[];
};

type SelectedFormat = VideoFormat & { format_id: string };

type DownloadJob = {
  job_id: string;
  status: "queued" | "downloading" | "complete" | "failed";
  progress: number | null;
  downloaded_bytes: number;
  total_bytes: number | null;
  filename: string | null;
  error: string | null;
};

const supportedPlatforms = [
  { name: "YouTube", icon: "/icons/youtube.svg", example: "youtube.com/watch?v=… · youtu.be/…", domains: ["youtube.com", "youtu.be", "youtube-nocookie.com"] },
  { name: "Facebook", icon: "/icons/facebook.svg", example: "facebook.com/reel/… · fb.watch/…", domains: ["facebook.com", "fb.watch"] },
  { name: "Instagram", icon: "/icons/instagram.svg", example: "instagram.com/reel/…", domains: ["instagram.com"] },
  { name: "TikTok", icon: "/icons/tik-tok.svg", example: "tiktok.com/@user/video/…", domains: ["tiktok.com"] },
  { name: "Discord", icon: "/icons/discord.svg", example: "discord.com/channels/… · public media link", domains: ["discord.com", "discordapp.com", "discordapp.net"] },
  { name: "Pinterest", icon: "/icons/pinterest.svg", example: "pinterest.com/pin/… · pin.it/…", domains: ["pinterest.com", "pin.it"] },
  { name: "Reddit", icon: "/icons/reddit.svg", example: "reddit.com/r/… · redd.it/…", domains: ["reddit.com", "redd.it"] },
  { name: "Threads", icon: "/icons/threads.svg", example: "threads.net/@user/post/…", domains: ["threads.net"] },
  { name: "X", icon: "/icons/x-twitter.svg", example: "x.com/user/status/…", domains: ["x.com", "twitter.com", "t.co"] },
];

export default function Home() {
  const videoUrlInput = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("YouTube");
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState<VideoAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFormatId, setSelectedFormatId] = useState("");
  const [isValidatingFormat, setIsValidatingFormat] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<SelectedFormat | null>(null);
  const [selectedOutputFormat, setSelectedOutputFormat] = useState("source");
  const [downloadJob, setDownloadJob] = useState<DownloadJob | null>(null);
  const [isStartingDownload, setIsStartingDownload] = useState(false);

  async function analyzeLink(rawValue: string) {
    const value = rawValue.trim();

    if (!value) {
      setMessage("Paste a video link to get started.");
      return;
    }

    try {
      const parsed = new URL(value);
      if ((parsed.protocol !== "http:" && parsed.protocol !== "https:") || !parsed.hostname) {
        setMessage("Enter a valid video URL beginning with http:// or https://.");
        return;
      }
      const selected = supportedPlatforms.find((platform) => platform.name === selectedPlatform);
      if (!selected) {
        setMessage("Choose a platform before analyzing the video link.");
        return;
      }
      const hostMatchesSelection = selected.domains.some((domain) =>
        parsed.hostname === domain || parsed.hostname.endsWith(`.${domain}`),
      );
      if (!hostMatchesSelection) {
        setMessage(`This link is not from ${selected.name}. Choose the matching platform or paste a ${selected.name} link.`);
        return;
      }
    } catch {
      setMessage("Enter a valid video URL beginning with http:// or https://.");
      return;
    }

    setIsAnalyzing(true);
    setMessage("");
    setAnalysis(null);
    setSelectedFormatId("");
    setSelectedFormat(null);
    setSelectedOutputFormat("source");
    setDownloadJob(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: value }),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail : "Could not analyze this link.");
      }

      setAnalysis(result as VideoAnalysis);
      const formats = (result as VideoAnalysis).formats;
      setSelectedFormatId(formats[0]?.format_id || "");
      setMessage("Video details found.");
    } catch (error) {
      setMessage(error instanceof TypeError
        ? "Could not reach the video service. Make sure the API is running and try again."
        : error instanceof Error ? error.message : "Could not analyze this link. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await analyzeLink(url);
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    const pastedValue = event.clipboardData.getData("text").trim();
    if (!pastedValue) return;

    event.preventDefault();
    setUrl(pastedValue);
    void analyzeLink(pastedValue);
  }

  async function handleFormatSelection() {
    if (!selectedFormatId) return;
    setIsValidatingFormat(true);
    setSelectedFormat(null);
    setMessage("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiUrl}/api/formats/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), format_id: selectedFormatId, output_format: "source" }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail : "That format is no longer available.");
      }
      setSelectedFormat(result.format as SelectedFormat);
      setSelectedOutputFormat("source");
      setDownloadJob(null);
      setMessage("Format selection confirmed.");
    } catch (error) {
      setMessage(error instanceof TypeError
        ? "Could not reach the video service. Make sure the API is running and try again."
        : error instanceof Error ? error.message : "Could not verify the selected format.");
    } finally {
      setIsValidatingFormat(false);
    }
  }

  async function handleStartDownload() {
    if (!selectedFormat || !selectedFormatId || isStartingDownload) return;
    setIsStartingDownload(true);
    setDownloadJob(null);
    setMessage("");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    try {
      const response = await fetch(`${apiUrl}/api/downloads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), format_id: selectedFormatId, output_format: selectedOutputFormat }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ? result.detail : "Could not start the download.");
      }

      let current = result as DownloadJob;
      setDownloadJob(current);
      while (current.status === "queued" || current.status === "downloading") {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        const statusResponse = await fetch(`${apiUrl}/api/downloads/${current.job_id}`, { cache: "no-store" });
        const statusResult = await statusResponse.json();
        if (!statusResponse.ok) {
          throw new Error(typeof statusResult.detail === "string" ? statusResult.detail : "Could not check the download status.");
        }
        current = statusResult as DownloadJob;
        setDownloadJob(current);
      }

      if (current.status === "failed") {
        setMessage(current.error || "The download failed. Try another available format.");
      } else if (current.status === "complete") {
        const downloadLink = document.createElement("a");
        downloadLink.href = `${apiUrl}/api/downloads/${current.job_id}/file`;
        downloadLink.style.display = "none";
        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
        setMessage("Your browser download has started.");
      }
    } catch (error) {
      setMessage(error instanceof TypeError
        ? "Could not reach the video service. Make sure the API is running and try again."
        : error instanceof Error ? error.message : "Could not complete the download.");
    } finally {
      setIsStartingDownload(false);
    }
  }

  function formatDuration(seconds: number | null) {
    if (seconds === null) return "Duration unavailable";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
  }

  function formatFileSize(bytes: number | null, isApprox = false) {
    if (bytes === null) return "Size unavailable";
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    return `${isApprox ? "~" : ""}${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  const isBusy = isAnalyzing || isValidatingFormat || isStartingDownload;

  return (
    <main className="landing-page">
      <header className="topbar">
        <a className="wordmark" href="#home" aria-label={`${siteConfig.name} home`}>
          {siteConfig.name.toUpperCase()}
        </a>
        <nav className="platform-nav" aria-label="Supported platforms">
          {supportedPlatforms.map((platform, index) => (
            <span className="platform-nav-item" key={platform.name}>
              {index > 0 && <span aria-hidden="true">|</span>}
              <a href="#platforms">{platform.name}</a>
            </span>
          ))}
        </nav>
      </header>

      <section className="hero" id="home" aria-labelledby="hero-title">
        <h1 id="hero-title">Free Online Video Downloader</h1>

        <form className="download-form" onSubmit={handleSubmit}>
          <label className="visually-hidden" htmlFor="video-url">
            {selectedPlatform} video link
          </label>
          <input
            id="video-url"
            ref={videoUrlInput}
            type="url"
            inputMode="url"
            placeholder="Paste link"
            value={url}
            disabled={isBusy}
            onPaste={handlePaste}
            onChange={(event) => {
              setUrl(event.target.value);
              setMessage("");
              setAnalysis(null);
              setSelectedFormatId("");
              setSelectedFormat(null);
              setSelectedOutputFormat("source");
              setDownloadJob(null);
            }}
            aria-describedby={message ? "form-message" : undefined}
          />
          <button type="submit" disabled={isBusy}>
            {isAnalyzing ? "Analyzing…" : "Analyze"}
          </button>
        </form>

        <p className="terms-copy">
          By using our service you accept our <a href="#terms">Terms of Service</a> and{" "}
          <a href="#privacy">Privacy Policy</a>
        </p>
        <p className="form-message" id="form-message" role="status" aria-live="polite">
          {isAnalyzing
            ? "Checking the video link…"
            : isStartingDownload && !downloadJob
              ? "Preparing your download…"
              : message}
        </p>

        {analysis && (
          <section className="video-preview" aria-label="Video details">
            {analysis.thumbnail && (
              // Metadata thumbnails may be served by any supported video platform.
              // eslint-disable-next-line @next/next/no-img-element
              <img
                className="video-thumbnail"
                src={analysis.thumbnail}
                alt=""
                loading="eager"
                referrerPolicy="no-referrer"
                onError={(event) => {
                  event.currentTarget.hidden = true;
                }}
              />
            )}
            <div className="video-details">
              <p className="video-platform">{analysis.platform} · {formatDuration(analysis.duration)}</p>
              <h2>{analysis.title}</h2>
              <p className="format-summary">
                {analysis.formats.length
                  ? `${analysis.formats.length} available source formats`
                  : "No downloadable formats were returned for this video."}
              </p>
              {analysis.formats.length > 0 && (
                <div className="format-picker">
                  <label htmlFor="format-choice">Available quality and format</label>
                  <select
                    id="format-choice"
                    value={selectedFormatId}
                    disabled={isBusy}
                    onChange={(event) => {
                      setSelectedFormatId(event.target.value);
                      setSelectedFormat(null);
                      setSelectedOutputFormat("source");
                      setDownloadJob(null);
                      setMessage("");
                    }}
                  >
                    {analysis.formats.map((format, index) => (
                      <option key={`${format.format_id}-${index}`} value={format.format_id || ""}>
                        {format.kind === "audio"
                          ? `Audio${format.ext ? ` · ${format.ext.toUpperCase()}` : ""}`
                          : `${format.height ? `${format.height}p` : "Video"}${format.ext ? ` · ${format.ext.toUpperCase()}` : ""}${format.has_audio ? " · audio" : " · video only"}`}
                        {` — ${formatFileSize(format.filesize, format.filesize_is_approx)}`}
                      </option>
                    ))}
                  </select>
                  <button
                    className="confirm-format-button"
                    type="button"
                    onClick={handleFormatSelection}
                    disabled={!selectedFormatId || isBusy}
                  >
                    {isValidatingFormat ? "Checking…" : "Use this format"}
                  </button>
                  {selectedFormat && (
                    <>
                      <p className="selected-format-message">
                        Selected: {selectedFormat.kind === "audio"
                          ? `Audio${selectedFormat.ext ? ` · ${selectedFormat.ext.toUpperCase()}` : ""}`
                          : `${selectedFormat.height ? `${selectedFormat.height}p` : "Video"}${selectedFormat.ext ? ` · ${selectedFormat.ext.toUpperCase()}` : ""}`}
                        {` · ${formatFileSize(selectedFormat.filesize, selectedFormat.filesize_is_approx)}`}
                      </p>
                      <label className="output-format-label" htmlFor="output-format-choice">Output format</label>
                      <select
                        id="output-format-choice"
                        value={selectedOutputFormat}
                        disabled={isStartingDownload || Boolean(downloadJob && ["queued", "downloading", "complete"].includes(downloadJob.status))}
                        onChange={(event) => {
                          setSelectedOutputFormat(event.target.value);
                          setDownloadJob(null);
                          setMessage("");
                        }}
                      >
                        {selectedFormat.output_formats.map((output) => (
                          <option key={output.id} value={output.id}>{output.label}</option>
                        ))}
                      </select>
                      <button
                        className="start-download-button"
                        type="button"
                        onClick={handleStartDownload}
                        disabled={isStartingDownload || downloadJob?.status === "complete" || Boolean(downloadJob && ["queued", "downloading"].includes(downloadJob.status))}
                      >
                        {downloadJob?.status === "complete"
                          ? "Sent to browser"
                          : downloadJob?.status === "downloading"
                            ? "Preparing video…"
                            : downloadJob?.status === "queued"
                              ? "Waiting to prepare…"
                              : downloadJob?.status === "failed"
                                ? "Try download again"
                                : isStartingDownload ? "Starting download…" : "Download selected format"}
                      </button>
                    </>
                  )}
                  {downloadJob && (downloadJob.status === "queued" || downloadJob.status === "downloading") && (
                    <div className="download-status" role="status" aria-live="polite">
                      <span>
                        {downloadJob.status === "queued"
                          ? "Waiting for a preparation slot…"
                          : `Preparing your ${analysis.platform} video…`}
                      </span>
                      {downloadJob.progress !== null && (
                        <>
                          <progress max="100" value={downloadJob.progress} aria-label="Download progress" />
                          <span>{Math.floor(downloadJob.progress)}%</span>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}

        <div className="rating" aria-label="Rated 4.8 out of 5 from 55 reviews">
          <span className="stars" aria-hidden="true">★★★★★</span>
          <span>4.8/5</span>
          <span className="rating-dot" aria-hidden="true">·</span>
          <span>55 reviews</span>
        </div>

        <section className="platform-picker-section" aria-labelledby="platform-picker-heading">
          <h2 className="platform-picker-heading" id="platform-picker-heading">
            Choose a platform <span>{selectedPlatform === "YouTube" ? "YouTube is selected by default" : `${selectedPlatform} selected`}</span>
          </h2>
          <div className="platform-choices" id="platforms" role="group" aria-label="Choose a video platform">
            {supportedPlatforms.map((platform) => (
              <button
                className={`platform-choice${selectedPlatform === platform.name ? " is-selected" : ""}`}
                type="button"
                key={platform.name}
                disabled={isBusy}
                aria-pressed={selectedPlatform === platform.name}
                onClick={() => {
                  setSelectedPlatform(platform.name);
                  setMessage("");
                  setAnalysis(null);
                  setSelectedFormatId("");
                  setSelectedFormat(null);
                  setSelectedOutputFormat("source");
                  setDownloadJob(null);
                  videoUrlInput.current?.focus();
                }}
              >
                {/* The SVGs are supplied local assets in public/icons. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={platform.icon} alt="" aria-hidden="true" />
                <span className="platform-choice-name">{platform.name}</span>
                <span className="platform-example">{platform.example}</span>
              </button>
            ))}
          </div>
          <p className="permission-note">
            Only download public videos you have permission to save. Private or login-restricted content may not be available.
          </p>
        </section>

      </section>
      <Policies />
      <footer className="site-footer">
        <span>© {siteConfig.name}</span>
        <nav aria-label="Legal information">
          <a href="#terms">Terms of Service</a>
          <a href="#privacy">Privacy Policy</a>
        </nav>
      </footer>
    </main>
  );
}
