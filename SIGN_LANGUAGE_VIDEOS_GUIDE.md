# Sign Language Video Integration Guide

## Overview
This Sign Language Translator now supports **real human sign language videos** performed by deaf interpreters and performers. The system can play authentic ASL videos for each word/phrase.

## Quick Start: Add Real Sign Language Videos

### Method 1: Manual Video Addition (Simple)

1. **Prepare your video files:**
   - Format: MP4, WebM, AVI, or MOV
   - Naming: `{word}.mp4` (e.g., `hello.mp4`, `thank-you.mp4`)
   - Location: Create folder structure like:
     ```
     your_videos/
     ├── hello.mp4
     ├── thank-you.mp4
     ├── please.mp4
     ├── good.mp4
     └── morning.mp4
     ```

2. **Python Script - Add Video Batch:**
   ```python
   from backend.sign_video_manager import import_video_batch
   
   # Add all videos from a folder
   import_video_batch('path/to/your_videos')
   
   # Or add single video:
   from backend.sign_video_manager import add_video_file
   add_video_file('hello', 'path/to/hello.mp4', gloss='HELLO')
   ```

3. **Restart the Flask server:**
   ```bash
   cd backend
   python app_v2.py
   ```

### Method 2: Automated Browser (YouTube Integration)

Coming soon: Script to download ASL videos from YouTube channels dedicated to sign language education.

## Free Sources for Real Sign Language Videos

### 1. **SignASL** (Recommended)
- Website: https://www.signasl.org/
- Free dictionary with ASL videos performed by native signers
- Download format: MP4
- Usage: All educational use

### 2. **ASLIZED** 
- Website: https://www.aslized.org/
- Sign language videos with text explanations
- Coverage: 5000+ words

### 3. **Handspeak**
- Website: https://www.handspeak.com/
- ASL dictionary with clear video demonstrations
- High-quality videos

### 4. **Sign Language Resources**
- Lifeprint ASL Dictionary: lifeprint.com
- ASL Connect: aslconnect.org (community videos)
- YouTube channels: "ASL That", "Signing Savvy", "Bill Vicars"

### 5. **Commercial Options**
- **Signing Savvy**: subscription ($10-15/month but has free tier)
- **ASL Dictionary**: premium app (but videos can be extracted)

## Video File Organization

### Directory Structure
```
static/
└── signs/
    ├── videos/                           # Real human videos
    │   ├── hello.mp4
    │   ├── thank-you.mp4
    │   ├── please.mp4
    │   └── ... (up to 1000s of videos)
    ├── videos_metadata.json              # Metadata index
    ├── sign_mapping.json                 # Word → Gloss mappings
    └── (placeholder PNGs as fallback)
```

## How to Download Videos Manually

### From SignASL:
1. Go to https://www.signasl.org/search
2. Search for a word (e.g., "hello")
3. Right-click the video → "Save video as"
4. Rename to lowercase: `hello.mp4`
5. Place in `static/signs/videos/`

### From YouTube:
Using `youtube-dl`:
```bash
pip install yt-dlp

# Download single video
yt-dlp -f best[ext=mp4] https://www.youtube.com/watch?v=VIDEO_ID -o "hello.mp4"

# Batch download from playlist
yt-dlp -f best[ext=mp4] https://www.youtube.com/playlist?list=PLAYLIST_ID -o "%(title)s.mp4"
```

## Video Format & Optimization

### Recommended Specifications:
- **Format**: MP4 (H.264 codec)
- **Resolution**: 640x480 or higher
- **Duration**: 2-5 seconds per sign
- **Framerate**: 30 FPS
- **Bitrate**: 500-2000 kbps (balance quality and size)

### Optimize Existing Videos (ffmpeg):
```bash
# Install ffmpeg
# Windows: choco install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg

# Convert and optimize video
ffmpeg -i input_video.mov \
  -c:v libx264 \
  -preset fast \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  output_hello.mp4
```

From Python:
```python
from backend.sign_video_manager import convert_to_mp4

convert_to_mp4('input_video.mov', 'hello.mp4')
```

## System Behavior

### Video URL Priority:
1. **Real Videos** (static/signs/videos/*.mp4)
   - Returns: `/static/signs/videos/hello.mp4`
   - Quality: ⭐⭐⭐⭐⭐ Human-performed
   
2. **Placeholder Images** (static/signs/*.png)
   - Returns: `/static/signs/hello.png`
   - Quality: ⭐ Text-based placeholder
   - Used when no real video available

### Example API Response:
```json
{
  "success": true,
  "gloss_line": "HELLO THANK-YOU PLEASE",
  "sign_sequence": [
    {
      "kind": "lexical",
      "gloss": "HELLO",
      "english": "hello",
      "video_url": "/static/signs/videos/hello.mp4"
    },
    {
      "kind": "lexical",
      "gloss": "THANK-YOU",
      "english": "thank you",
      "video_url": "/static/signs/videos/thank-you.mp4"
    }
  ]
}
```

## Batch Processing Multiple Videos

### Upload from Directory:
```bash
# Copy all videos to the system
python -c "
from backend.sign_video_manager import import_video_batch
import_video_batch('/path/to/video_library')
"
```

### Check Current Videos:
```bash
python -c "
from backend.sign_video_manager import list_available_videos
list_available_videos()
"
```

## Troubleshooting

### Problem: "No matching files in static/signs"
**Solution**: 
1. Check if videos are in `static/signs/videos/` folder
2. Verify filenames match word list
3. Restart Flask server

### Problem: "Video won't play in browser"
**Solution**:
1. Convert to MP4: `ffmpeg -i video.mov -c:v h264 output.mp4`
2. Check browser compatibility (MP4 works best)
3. Install codec pack if needed

### Problem: "MetaData not updating"
**Solution**:
1. Delete `static/signs/videos_metadata.json`
2. Restart Flask server
3. Re-run import script

## Advanced: Custom Video Naming

The system matches videos by these priority rules:
1. Exact English word match (e.g., "hello" → hello.mp4)
2. Gloss with hyphens (e.g., "THANK-YOU" → thank-you.mp4)
3. Gloss without separators (e.g., "HELLO" → hello.mp4)
4. Fallback to placeholder PNG

Example video naming that all work:
```
For word "hello":
  ✓ hello.mp4
  ✓ HELLO.mp4

For phrase "thank you" (gloss THANK-YOU):
  ✓ thank-you.mp4
  ✓ thankyou.mp4
  ✓ THANK-YOU.mp4
  ✓ thank.mp4 (partial match)
```

## Performance Tips

### For Large Video Library (100s-1000s):
1. Use MP4 format with H.264 (smallest size)
2. Optimize bitrate: 800-1200 kbps
3. Create playlist cache in metadata
4. Use CDN for video streaming

### Storage Estimation:
- 1 minute video @ 1 Mbps = ~7.5 MB
- 100 signs × 3 sec @ 15 Mbps = ~56 MB
- 1000 signs @ 15 Mbps = 560 MB

## Next Steps

1. **Get Videos**: Download from SignASL or other sources
2. **Organize**: Place in `static/signs/videos/` with proper names
3. **Import**: Run the import script
4. **Test**: Restart server and try text → sign translation
5. **Optimize**: Convert videos to MP4 if needed

## Help & Support

For questions about specific sign language resources or video formats:
- ASL Community: https://www.reddit.com/r/asl/
- SignASL Forum: https://www.signasl.org/
- FFmpeg Documentation: https://ffmpeg.org/

---

**Updated**: System now fully supports real human sign language videos!
Test it by adding your first video and typing its corresponding word.
