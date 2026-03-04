"""
TikTokBatchFactory - Batch TikTok Video Generator
Client: Tiana M. | Budget: $100
Reads Google Sheet -> Downloads assets from Drive -> Renders vertical TikTok videos with NVIDIA GPU
"""

import os
import sys
import re
import subprocess
import json
import textwrap
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gdown
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# -----------------------------------------------
# LOAD CONFIG FROM config.py (works for both .py and .exe)
# -----------------------------------------------
def _get_base_dir():
    """Get the directory where the exe or script lives."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).parent.resolve()

# Add base dir to sys.path so config.py is found next to the EXE
_base = _get_base_dir()
if str(_base) not in sys.path:
    sys.path.insert(0, str(_base))

import config as cfg

CONFIG = {
    "SHEET_NAME": cfg.SHEET_NAME,
    "WORKSHEET_INDEX": cfg.WORKSHEET_INDEX,
    "CREDENTIALS_PATH": os.path.join(cfg.CREDENTIALS_FOLDER, cfg.CREDENTIALS_FILENAME),
    "WIDTH": cfg.VIDEO_WIDTH,
    "HEIGHT": cfg.VIDEO_HEIGHT,
    "CODEC": cfg.VIDEO_CODEC,
    "PRESET": cfg.GPU_PRESET,
    "CQ": str(cfg.VIDEO_QUALITY),
    "AUDIO_BITRATE": cfg.AUDIO_BITRATE,
    "FPS": cfg.VIDEO_FPS,
    "FONT_DIR": cfg.FONT_FOLDER,
    "FONT_SIZE": cfg.FONT_SIZE,
    "FONT_COLOR": cfg.FONT_COLOR,
    "FONT_BORDER_COLOR": cfg.FONT_BORDER_COLOR,
    "FONT_BORDER_WIDTH": cfg.FONT_BORDER_WIDTH,
    "TEXT_POSITION_Y": cfg.TEXT_POSITION_Y,
    "OUTPUT_DIR": cfg.OUTPUT_FOLDER,
    "TEMP_DIR": cfg.TEMP_FOLDER,
}

console = Console(force_terminal=True)

# -----------------------------------------------
# UTILITY FUNCTIONS
# -----------------------------------------------

def get_script_dir():
    """Get the directory where this script or EXE lives."""
    return _base


def check_ffmpeg():
    """Verify FFmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            console.print(f"[green][OK] FFmpeg found:[/green] {version_line}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    console.print("[red][FAIL] FFmpeg not found! Please install FFmpeg and add it to PATH.[/red]")
    console.print("[yellow]  Download: https://www.gyan.dev/ffmpeg/builds/[/yellow]")
    return False


def check_nvidia_gpu():
    """Check if NVIDIA GPU encoding actually works (not just listed in FFmpeg)."""
    try:
        # Actually try encoding a tiny test frame with nvenc
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
                "-c:v", "h264_nvenc", "-f", "null", "-"
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            console.print("[green][OK] NVIDIA GPU encoder (h264_nvenc) working[/green]")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    console.print("[yellow][WARN] NVIDIA GPU encoder (h264_nvenc) not available on this machine.[/yellow]")
    console.print("[yellow]  Using CPU encoding (libx264) -- slower but works everywhere.[/yellow]")
    return False


def find_font():
    """Find the first .ttf or .otf font file in the fonts/ directory."""
    script_dir = get_script_dir()
    font_dir = script_dir / CONFIG["FONT_DIR"]

    if not font_dir.exists():
        font_dir.mkdir(exist_ok=True)
        console.print(f"[red][FAIL] No font found! Place a .ttf or .otf file in: {font_dir}[/red]")
        return None

    for ext in ["*.ttf", "*.otf", "*.TTF", "*.OTF"]:
        fonts = list(font_dir.glob(ext))
        if fonts:
            font_path = fonts[0]
            console.print(f"[green][OK] Font found:[/green] {font_path.name}")
            return str(font_path)

    console.print(f"[red][FAIL] No font found! Place a .ttf or .otf file in: {font_dir}[/red]")
    return None


def extract_drive_id(url):
    """Extract Google Drive file ID from various URL formats."""
    if not url:
        return None

    url = url.strip()

    # Format: https://drive.google.com/file/d/FILE_ID/view...
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # Format: https://drive.google.com/open?id=FILE_ID
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # Format: direct file ID (no URL, just the ID)
    if re.match(r'^[a-zA-Z0-9_-]{20,}$', url):
        return url

    return None


def download_from_drive(url, output_path):
    """Download a file from Google Drive using gdown."""
    file_id = extract_drive_id(url)
    if not file_id:
        console.print(f"[red]  [FAIL] Invalid Google Drive URL: {url}[/red]")
        return False

    drive_url = f"https://drive.google.com/uc?id={file_id}"

    try:
        gdown.download(drive_url, output_path, quiet=True, fuzzy=True)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            console.print(f"[red]  [FAIL] Download failed or empty file: {url}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]  [FAIL] Download error: {e}[/red]")
        return False


def escape_text_for_ffmpeg(text):
    """Escape special characters for FFmpeg drawtext filter."""
    if not text:
        return ""
    # FFmpeg drawtext requires escaping these characters
    text = text.replace("\\", "\\\\\\\\")
    text = text.replace("'", "'\\\\\\''")
    text = text.replace("%", "%%")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace(";", "\\;")
    return text


def get_video_info(video_path):
    """Get video dimensions and duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path
            ],
            capture_output=True, text=True, timeout=30
        )
        info = json.loads(result.stdout)
        stream = info.get("streams", [{}])[0]
        fmt = info.get("format", {})

        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))
        duration = float(stream.get("duration", 0) or fmt.get("duration", 0))

        return {"width": width, "height": height, "duration": duration}
    except Exception as e:
        console.print(f"[yellow]  [WARN] Could not read video info: {e}[/yellow]")
        return {"width": 0, "height": 0, "duration": 0}


def get_audio_duration(audio_path):
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                audio_path
            ],
            capture_output=True, text=True, timeout=30
        )
        info = json.loads(result.stdout)
        return float(info.get("format", {}).get("duration", 0))
    except Exception:
        return 0


# -----------------------------------------------
# CORE VIDEO RENDERING
# -----------------------------------------------

def render_video(video_path, audio_path, text, font_path, output_path, use_gpu=True):
    """
    Render a single TikTok video:
    1. Auto-crop/resize input video to 9:16 (1080x1920)
    2. Add static text overlay slightly below center
    3. Replace audio with song file
    4. Encode with NVIDIA GPU (h264_nvenc)
    """
    w = CONFIG["WIDTH"]
    h = CONFIG["HEIGHT"]
    codec = CONFIG["CODEC"] if use_gpu else "libx264"
    escaped_text = escape_text_for_ffmpeg(text)

    # Escape font path for FFmpeg (Windows backslashes -> forward slashes, escape colons)
    ffmpeg_font_path = font_path.replace("\\", "/").replace(":", "\\:")

    # Build video filter chain:
    # 1. Scale to fill 1080x1920 (crop to center if aspect ratio differs)
    # 2. Add text overlay at configured vertical position
    video_filter = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        f"setsar=1"
    )

    # Add text overlay with automatic word-wrapping for long captions
    if text and text.strip():
        text_y = CONFIG["TEXT_POSITION_Y"]
        font_size = CONFIG["FONT_SIZE"]

        # Calculate max characters per line based on font size and video width
        padding = 100  # pixels margin on each side
        avg_char_width = font_size * 0.55  # approximate average character width
        max_chars = int((w - padding) / avg_char_width)
        max_chars = max(max_chars, 10)  # minimum 10 chars per line

        # Word-wrap text into multiple lines
        lines = textwrap.wrap(text.strip(), width=max_chars)
        if not lines:
            lines = [text.strip()]

        # Calculate vertical spacing
        line_height = int(font_size * 1.4)  # 1.4x font size for comfortable line spacing
        total_height = len(lines) * line_height
        half_height = total_height // 2

        # Add a separate drawtext filter for each line (each line centered independently)
        for i, line in enumerate(lines):
            escaped_line = escape_text_for_ffmpeg(line)
            y_offset = i * line_height
            video_filter += (
                f",drawtext="
                f"fontfile='{ffmpeg_font_path}':"
                f"text='{escaped_line}':"
                f"fontsize={font_size}:"
                f"fontcolor={CONFIG['FONT_COLOR']}:"
                f"borderw={CONFIG['FONT_BORDER_WIDTH']}:"
                f"bordercolor={CONFIG['FONT_BORDER_COLOR']}:"
                f"x=(w-text_w)/2:"
                f"y=h*{text_y}-{half_height}+{y_offset}"
            )

    # Get video duration — video defines the output length
    video_info = get_video_info(video_path)
    video_duration = video_info["duration"]

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1",   # Loop audio if shorter than video
        "-i", audio_path,
        "-vf", video_filter,
        "-map", "0:v:0",        # Use video from first input
        "-map", "1:a:0",        # Use audio from second input
        "-c:v", codec,
        "-c:a", "aac",
        "-b:a", CONFIG["AUDIO_BITRATE"],
        "-r", str(CONFIG["FPS"]),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]

    # GPU-specific settings
    if use_gpu:
        cmd.extend(["-preset", CONFIG["PRESET"], "-cq", CONFIG["CQ"]])
    else:
        cmd.extend(["-preset", "medium", "-crf", CONFIG["CQ"]])

    # Video defines the output length — trim everything to video duration
    if video_duration > 0:
        cmd.extend(["-t", str(video_duration)])

    cmd.append(output_path)

    # Run FFmpeg
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=600  # 10 min timeout per video
        )
        if result.returncode != 0:
            console.print(f"[red]  [FAIL] FFmpeg error:[/red]")
            # Show last few lines of error
            error_lines = result.stderr.strip().split("\n")[-5:]
            for line in error_lines:
                console.print(f"[dim]    {line}[/dim]")
            return False

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    except subprocess.TimeoutExpired:
        console.print("[red]  [FAIL] Render timed out (>10 minutes)[/red]")
        return False
    except Exception as e:
        console.print(f"[red]  [FAIL] Render error: {e}[/red]")
        return False


# -----------------------------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------------------------

def connect_to_sheet():
    """Connect to Google Sheets using service account credentials."""
    script_dir = get_script_dir()
    creds_path = script_dir / CONFIG["CREDENTIALS_PATH"]

    if not creds_path.exists():
        console.print(f"[red][FAIL] Credentials file not found: {creds_path}[/red]")
        console.print("[yellow]  Copy your service_account.json to the credentials/ folder.[/yellow]")
        console.print(f"[yellow]  Expected: {CONFIG['CREDENTIALS_PATH']}[/yellow]")
        return None

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(str(creds_path), scope)
        client = gspread.authorize(creds)
        sheet = client.open(CONFIG["SHEET_NAME"]).get_worksheet(CONFIG["WORKSHEET_INDEX"])
        console.print(f"[green][OK] Connected to Google Sheet:[/green] {CONFIG['SHEET_NAME']}")
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        console.print(f"[red][FAIL] Sheet '{CONFIG['SHEET_NAME']}' not found![/red]")
        console.print("[yellow]  Make sure you shared the sheet with your service account email.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red][FAIL] Google Sheets error: {e}[/red]")
        return None


def read_sheet_data(sheet):
    """Read all rows from the Google Sheet. Expected columns: Song URL, Video URL, Text on screen."""
    try:
        all_rows = sheet.get_all_records()
        if not all_rows:
            console.print("[yellow][WARN] Sheet is empty -- no rows to process.[/yellow]")
            return []

        # Normalize column names (strip whitespace, lowercase for matching)
        valid_rows = []
        for i, row in enumerate(all_rows):
            # Try to find columns by flexible matching
            keys = list(row.keys())
            song_url = None
            video_url = None
            text = None

            for key in keys:
                k = key.strip().lower()
                if "song" in k and "url" in k:
                    song_url = str(row[key]).strip()
                elif "video" in k and "url" in k:
                    video_url = str(row[key]).strip()
                elif "text" in k:
                    text = str(row[key]).strip()

            # Fallback: use column position (A=Song URL, B=Video URL, C=Text)
            if song_url is None and len(keys) >= 1:
                song_url = str(row[keys[0]]).strip()
            if video_url is None and len(keys) >= 2:
                video_url = str(row[keys[1]]).strip()
            if text is None and len(keys) >= 3:
                text = str(row[keys[2]]).strip()

            if song_url and video_url:
                valid_rows.append({
                    "row_num": i + 2,  # +2 for header row + 0-index
                    "song_url": song_url,
                    "video_url": video_url,
                    "text": text or ""
                })
            else:
                console.print(f"[yellow]  [WARN] Row {i + 2} skipped (missing Song URL or Video URL)[/yellow]")

        return valid_rows

    except Exception as e:
        console.print(f"[red][FAIL] Error reading sheet data: {e}[/red]")
        return []


# -----------------------------------------------
# CLEANUP
# -----------------------------------------------

def cleanup_temp(temp_dir):
    """Delete all temporary files in the temp directory."""
    try:
        for f in Path(temp_dir).iterdir():
            if f.name == ".gitkeep":
                continue
            if f.is_file():
                f.unlink()
    except Exception:
        pass


# -----------------------------------------------
# MAIN BATCH PROCESSOR
# -----------------------------------------------

def main():
    script_dir = get_script_dir()
    os.chdir(script_dir)

    # Banner
    console.print(Panel.fit(
        "[bold cyan]TikTokBatchFactory[/bold cyan]\n"
        "[dim]Batch TikTok Video Generator -- NVIDIA GPU Accelerated[/dim]",
        border_style="cyan"
    ))
    console.print()

    # -- Pre-flight checks --
    console.print("[bold]Running pre-flight checks...[/bold]")

    if not check_ffmpeg():
        sys.exit(1)

    use_gpu = check_nvidia_gpu()

    font_path = find_font()
    if not font_path:
        sys.exit(1)

    # -- Connect to Google Sheet --
    console.print()
    console.print("[bold]Connecting to Google Sheet...[/bold]")
    sheet = connect_to_sheet()
    if not sheet:
        sys.exit(1)

    # -- Read rows --
    rows = read_sheet_data(sheet)
    if not rows:
        console.print("[yellow]No valid rows found. Exiting.[/yellow]")
        sys.exit(0)

    console.print(f"\n[bold green]Found {len(rows)} video(s) to process.[/bold green]\n")

    # Show summary table
    table = Table(title="Batch Queue")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Text", style="white", max_width=50)
    table.add_column("Status", style="dim")
    for i, row in enumerate(rows):
        display_text = row["text"][:47] + "..." if len(row["text"]) > 50 else row["text"]
        table.add_row(str(i + 1), display_text or "(no text)", "Pending")
    console.print(table)
    console.print()

    # -- Setup directories --
    output_dir = script_dir / CONFIG["OUTPUT_DIR"]
    temp_dir = script_dir / CONFIG["TEMP_DIR"]
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)

    # -- Process each row --
    success_count = 0
    fail_count = 0

    for i, row in enumerate(tqdm(rows, desc="Rendering videos", unit="video")):
        video_num = i + 1
        console.print(f"\n[bold cyan]=== Video {video_num}/{len(rows)} ===[/bold cyan]")
        console.print(f"  Text: [white]{row['text'] or '(none)'}[/white]")

        # Temp file paths
        temp_video = str(temp_dir / f"video_{video_num}.mp4")
        temp_audio = str(temp_dir / f"audio_{video_num}.mp3")
        output_file = str(output_dir / f"video_{video_num:03d}.mp4")

        # Step 1: Download video
        console.print("  [dim]Downloading video...[/dim]", end=" ")
        if not download_from_drive(row["video_url"], temp_video):
            console.print("[red]FAILED[/red]")
            fail_count += 1
            cleanup_temp(temp_dir)
            continue
        console.print("[green]OK[/green]")

        # Step 2: Download audio
        console.print("  [dim]Downloading audio...[/dim]", end=" ")
        if not download_from_drive(row["song_url"], temp_audio):
            console.print("[red]FAILED[/red]")
            fail_count += 1
            cleanup_temp(temp_dir)
            continue
        console.print("[green]OK[/green]")

        # Step 3: Render video
        console.print("  [dim]Rendering with FFmpeg...[/dim]", end=" ")
        if render_video(temp_video, temp_audio, row["text"], font_path, output_file, use_gpu):
            console.print("[green]OK[/green]")
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            console.print(f"  [green][OK] Saved:[/green] {output_file} ({file_size:.1f} MB)")
            success_count += 1
        else:
            console.print("[red]FAILED[/red]")
            fail_count += 1

        # Step 4: Cleanup temp files for this video
        cleanup_temp(temp_dir)

    # -- Final summary --
    console.print(f"\n[bold]{'=' * 50}[/bold]")
    console.print(Panel.fit(
        f"[bold green][OK] Completed: {success_count}[/bold green]\n"
        f"[bold red][FAIL] Failed: {fail_count}[/bold red]\n"
        f"[bold]Total: {len(rows)}[/bold]\n\n"
        f"[dim]Output folder: {output_dir}[/dim]",
        title="[bold cyan]Batch Complete[/bold cyan]",
        border_style="cyan"
    ))

    if fail_count > 0:
        console.print("\n[yellow]Some videos failed. Check the error messages above.[/yellow]")

    console.print("\n[dim]Press Enter to exit...[/dim]")
    try:
        input()
    except EOFError:
        pass


if __name__ == "__main__":
    main()
