# TikTokBatchFactory

Batch TikTok video generator for Windows 10. Reads a Google Sheet, downloads assets from Google Drive, and renders vertical TikTok videos (1080x1920) with NVIDIA GPU acceleration.

---

## Features

- Reads Google Sheet with 3 columns: Song URL, Video URL, Text on screen
- Downloads video and audio from Google Drive (public/shared links)
- Auto-crops/resizes any video to vertical 9:16 (1080x1920)
- Adds static text overlay with custom font (slightly below center)
- Replaces original audio with song file
- NVIDIA GPU encoding (h264_nvenc) for fast rendering
- Bulk processes all rows automatically
- Auto-deletes temporary files after each render
- Colored console output with progress bar
- One double-click to run everything

---

## Installation (Step by Step)

### Step 1: Install Python

1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.10 or newer**
3. Run the installer
4. **IMPORTANT**: Check the box **"Add Python to PATH"** at the bottom of the installer
5. Click "Install Now"
6. Verify: Open Command Prompt and type:
   ```
   python --version
   ```
   You should see something like `Python 3.12.x`

### Step 2: Install FFmpeg

1. Go to **https://www.gyan.dev/ffmpeg/builds/**
2. Download the **"ffmpeg-release-essentials.zip"** (under Release builds)
3. Extract the ZIP file
4. Inside, find the `bin` folder containing `ffmpeg.exe`
5. Copy the **full path** to the `bin` folder (e.g., `C:\ffmpeg\bin`)
6. Add it to your system PATH:
   - Press **Win + S**, search for **"Environment Variables"**
   - Click **"Edit the system environment variables"**
   - Click **"Environment Variables"** button
   - Under **"System variables"**, find **"Path"** and click **Edit**
   - Click **"New"** and paste the path to the `bin` folder
   - Click **OK** on all windows
7. Verify: Open a **new** Command Prompt and type:
   ```
   ffmpeg -version
   ```

### Step 3: Check NVIDIA GPU

1. Make sure you have an NVIDIA GPU (GTX 1050 or newer recommended)
2. Update your GPU drivers: **https://www.nvidia.com/drivers**
3. Verify: Open Command Prompt and type:
   ```
   nvidia-smi
   ```
   You should see your GPU name and driver version

### Step 4: Install Python Dependencies

**Option A** (Easiest): Double-click `install.bat`

**Option B** (Manual): Open Command Prompt in the project folder and run:
```
pip install -r requirements.txt
```

### Step 5: Create Google Service Account

This is needed to read your Google Sheet automatically.

1. Go to **https://console.cloud.google.com/**
2. Create a new project (or use existing one)
3. Enable these APIs:
   - **Google Sheets API** — Search for it in the API Library and click Enable
   - **Google Drive API** — Search for it in the API Library and click Enable
4. Go to **IAM & Admin → Service Accounts**
5. Click **"Create Service Account"**
   - Name: `tiktok-batch` (or anything you want)
   - Click **Create and Continue**
   - Skip the optional steps, click **Done**
6. Click on the service account you just created
7. Go to the **"Keys"** tab
8. Click **Add Key → Create new key → JSON**
9. A `.json` file will download — this is your credentials file
10. **Rename it** to `service_account.json`
11. **Move it** to the `credentials/` folder in this project

### Step 6: Setup Your Google Sheet

1. Create a new Google Sheet
2. **Name it exactly**: `TikTokBatchFactory`
3. Set up 3 columns in Row 1 (header row):

   | A | B | C |
   |---|---|---|
   | Song URL | Video URL | Text on screen |

4. Fill in your rows starting from Row 2:
   - **Song URL**: Google Drive share link to the audio/song file
   - **Video URL**: Google Drive share link to the video file
   - **Text on screen**: The text to overlay on the video

5. **Share the sheet** with your service account email:
   - Find the email in your `service_account.json` (the `client_email` field)
   - It looks like: `tiktok-batch@your-project.iam.gserviceaccount.com`
   - Click **Share** on your Google Sheet and add this email as a **Viewer**

6. **Make sure your Google Drive files are accessible**:
   - Right-click each file in Google Drive → Share → **"Anyone with the link"** → **Viewer**

### Step 7: Place Your Font

1. Find a `.ttf` or `.otf` font file you want to use
2. Copy it into the `fonts/` folder
3. The script will automatically use the first font it finds

---

## Usage

### Quick Start
Double-click **`run.bat`** — that's it!

### What Happens
1. Script connects to your Google Sheet
2. Downloads all video and audio files from Google Drive
3. For each row: creates a vertical TikTok video (1080x1920)
4. Adds your text with your custom font
5. Encodes with NVIDIA GPU (fast!)
6. Saves to the `Output/` folder as `video_001.mp4`, `video_002.mp4`, etc.
7. Cleans up temporary files automatically

---

## Folder Structure

```
TikTokBatchFactory/
├── credentials/
│   └── service_account.json      ← Your Google credentials (Step 5)
├── fonts/
│   └── YourFont.ttf              ← Your custom font (Step 7)
├── Output/
│   └── video_001.mp4             ← Generated videos appear here
├── temp/                          ← Temporary files (auto-cleaned)
├── main.py                        ← Main script
├── requirements.txt               ← Python dependencies
├── run.bat                        ← Double-click to run
├── install.bat                    ← Double-click to install dependencies
└── README.md                      ← This file
```

---

## Configuration

You can edit settings at the top of `main.py` in the `CONFIG` dictionary:

| Setting | Default | Description |
|---|---|---|
| `SHEET_NAME` | `TikTokBatchFactory` | Name of your Google Sheet |
| `FONT_SIZE` | `54` | Text size on video |
| `FONT_COLOR` | `white` | Text color |
| `FONT_BORDER_WIDTH` | `3` | Text outline thickness |
| `CODEC` | `h264_nvenc` | GPU encoder (auto-falls back to CPU) |
| `CQ` | `23` | Quality (lower = better, 18-28 range) |
| `FPS` | `30` | Output frame rate |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Python not found" | Reinstall Python with "Add to PATH" checked |
| "FFmpeg not found" | Add FFmpeg `bin` folder to system PATH |
| "h264_nvenc not available" | Update NVIDIA drivers; script will fall back to CPU |
| "Sheet not found" | Check sheet name matches `SHEET_NAME` in config |
| "Permission denied on sheet" | Share sheet with service account email |
| "Download failed" | Make sure Drive files are set to "Anyone with the link" |
| "No font found" | Place a .ttf or .otf file in the `fonts/` folder |

---

## Requirements

- Windows 10/11
- Python 3.10+
- FFmpeg (with h264_nvenc support)
- NVIDIA GPU with updated drivers
- Google account (for Sheets API)
- Internet connection (for downloading files)
