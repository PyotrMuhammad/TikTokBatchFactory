"""
================================================================
        TikTokBatchFactory -- CONFIGURATION FILE

  Edit the values below to match your setup.
  Do NOT change the variable names (left side of "=").
  Only change the values (right side of "=").
================================================================
"""

# ──────────────────────────────────────────────
# GOOGLE SHEETS SETTINGS
# ──────────────────────────────────────────────

# The exact name of your Google Sheet (as it appears in Google Sheets)
SHEET_NAME = "TikTokBatchFactory"

# Which tab to read (0 = first tab, 1 = second tab, etc.)
WORKSHEET_INDEX = 0

# ──────────────────────────────────────────────
# GOOGLE CREDENTIALS
# ──────────────────────────────────────────────

# Name of your service account JSON file inside the "credentials" folder
# Example: "service_account.json" or "tiktok-488305-2a8205a4c452.json"
CREDENTIALS_FILENAME = "service_account.json"

# ──────────────────────────────────────────────
# VIDEO OUTPUT SETTINGS
# ──────────────────────────────────────────────

# TikTok vertical video resolution (do not change unless you know what you're doing)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Frames per second (30 is standard for TikTok)
VIDEO_FPS = 30

# Video quality: lower = better quality but bigger file (recommended: 18-28)
VIDEO_QUALITY = 23

# Audio quality (192k is good for music)
AUDIO_BITRATE = "192k"

# ──────────────────────────────────────────────
# GPU ENCODING SETTINGS
# ──────────────────────────────────────────────

# NVIDIA GPU encoder (do not change unless you have issues)
# "h264_nvenc" = NVIDIA GPU (fast)
# "libx264" = CPU fallback (slow but always works)
VIDEO_CODEC = "h264_nvenc"

# NVENC speed preset: p1=fastest, p4=balanced, p7=best quality
GPU_PRESET = "p4"

# ──────────────────────────────────────────────
# TEXT OVERLAY SETTINGS
# ──────────────────────────────────────────────

# Text size on the video (bigger number = bigger text)
FONT_SIZE = 54

# Text color (common options: white, yellow, red, blue, green, black)
FONT_COLOR = "white"

# Text border/outline color (helps text stand out on any background)
FONT_BORDER_COLOR = "black"

# Text border thickness (0 = no border, 3 = medium, 5 = thick)
FONT_BORDER_WIDTH = 3

# Text vertical position (0.5 = center, 0.55 = slightly below center, 0.7 = lower)
TEXT_POSITION_Y = 0.55

# ──────────────────────────────────────────────
# FOLDER NAMES (change only if you want different folder names)
# ──────────────────────────────────────────────

# Folder where your .ttf or .otf font file goes
FONT_FOLDER = "fonts"

# Folder where finished videos are saved
OUTPUT_FOLDER = "Output"

# Folder for temporary downloads (auto-cleaned after each video)
TEMP_FOLDER = "temp"

# Folder where your Google credentials JSON file is stored
CREDENTIALS_FOLDER = "credentials"
