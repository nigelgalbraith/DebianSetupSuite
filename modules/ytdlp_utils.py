#!/usr/bin/env python3
"""
ytdlp_utils.py

yt-dlp helpers.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

# ---------------------------------------------------------------------
# Supported audio and video formats for yt-dlp downloads.
# ---------------------------------------------------------------------

AUDIO_FORMATS = {
    "mp3",
    "aac",
    "flac",
    "m4a",
    "opus",
    "vorbis",
    "wav",
    "alac",
}

VIDEO_FORMATS = {
    "mp4",
    "mkv",
    "webm",
}

# ---------------------------------------------------------------------
# YT-DLP
# ---------------------------------------------------------------------


def run_yt_dlp(
    playlist_url: str,
    download_path: str,
    download_format: str,
    browser: str = "chromium",
) -> bool:
    """Download a playlist with yt-dlp using browser cookies."""
    if not playlist_url or not download_path or not download_format:
        print("[ERROR] Playlist URL, download path, and format are required.")
        return False
    download_dir = Path(download_path).expanduser()
    archive_file = download_dir / ".download_archive.txt"
    download_format = download_format.lower()
    if download_format not in AUDIO_FORMATS | VIDEO_FORMATS:
        print(f"[ERROR] Unsupported download format: {download_format}")
        return False
    try:
        download_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as e:
        print(f"[ERROR] Failed to create download directory: {e}")
        return False
    cmd = [
        "yt-dlp",
        "--cookies-from-browser",
        browser,
        "--download-archive",
        str(archive_file),
    ]
    if download_format in AUDIO_FORMATS:
        cmd.extend([
            "--extract-audio",
            "--audio-format",
            download_format,
        ])
    else:
        cmd.extend([
            "--merge-output-format",
            download_format,
        ])
    cmd.extend([
        "-P",
        str(download_dir),
        playlist_url,
    ])
    try:
        result = subprocess.run(cmd)
    except FileNotFoundError:
        print("[ERROR] yt-dlp was not found.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run yt-dlp: {e}")
        return False
    if result.returncode != 0:
        print(
            f"[ERROR] yt-dlp failed with exit code "
            f"{result.returncode}."
        )
        print(
            "[HINT] If authentication is required, "
            f"log into YouTube in {browser} and try again."
        )
        return False
    print(f"[OK] Download complete: {download_dir}")
    return True
