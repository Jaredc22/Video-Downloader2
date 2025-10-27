import os
import shutil
from pathlib import Path
from yt_dlp import YoutubeDL

DOWNLOAD_DIR = Path("./downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def _ffmpeg_path():
    # Detect ffmpeg on the container/host
    return shutil.which("ffmpeg")

def download_youtube(url: str, audio_only: bool = False, resolution: str = "1080", download_path: str | None = None):
    """
    Returns: (ok: bool, filepath_or_none: str|None, message: str)
    """
    if not url:
        return False, None, "❌ No URL provided."

    # Where to save
    out_dir = Path(os.path.expanduser(download_path or DOWNLOAD_DIR))
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "%(title)s.%(ext)s")

    ffmpeg = _ffmpeg_path()
    have_ffmpeg = ffmpeg is not None

    # Base options
    ydl_opts = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    if have_ffmpeg:
        ydl_opts["ffmpeg_location"] = ffmpeg  # tell yt-dlp explicitly

    # Format logic:
    if audio_only:
        if have_ffmpeg:
            # Produce MP3 (needs ffmpeg)
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            # Fallback: no merge, no transcode → m4a/webm as provided
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio/best"
            })
    else:
        if have_ffmpeg:
            # Try QT-friendly H.264 MP4 first, then fall back if unavailable
            format_chain = (
                f"bestvideo[ext=mp4][vcodec^=avc1][height<={resolution}]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={resolution}]+bestaudio/"
                "best"
            )
            ydl_opts.update({
                "format": format_chain,
                "merge_output_format": "mp4",
                "postprocessors": [
                    {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}
                ],
            })
        else:
            # Fallback: single, already-muxed stream to avoid merge
            ydl_opts.update({
                "format": "best[ext=mp4]/best"
            })

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Resolve output path yt-dlp actually wrote
            if "requested_downloads" in info and info["requested_downloads"]:
                filename = info["requested_downloads"][0].get("filepath")
            else:
                filename = ydl.prepare_filename(info)
        return True, filename, "✅ Download complete."
    except Exception as e:
        # Make the ffmpeg situation crystal clear
        if "ffmpeg" in str(e).lower() and not have_ffmpeg:
            return False, None, "❌ FFmpeg is not available. Using fallback: set Audio Only OFF or accept M4A/WEBM for audio."
        return False, None, f"❌ Error: {e}"
