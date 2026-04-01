# How to Switch to Video-Enabled Sign Language Translator

## Current Status
- **Default**: Using placeholder PNG images
- **Enhanced**: Switch to `app_v2.py` to use real sign language videos

## Quick Switch (2 minutes)

### Step 1: Rename Current App
```bash
# Backup the current app
cd backend
mv app.py app_original.py
mv text_to_sign.py text_to_sign_original.py
```

### Step 2: Use Video-Enabled Version
```bash
# Copy the video-enabled versions
cp app_v2.py app.py
cp text_to_sign_v2.py text_to_sign.py
```

### Step 3: Restart Flask Server
```bash
# Kill old server (Ctrl+C) and start new one
python app.py
```

Done! Now your system is ready for real sign language videos.

## Setup Real Videos (5-10 minutes)

### Option A: Download from SignASL (Easiest)

1. Go to https://www.signasl.org/
2. Search for a word (e.g., "hello")
3. Right-click video → "Save video as"
4. Save to: `static/signs/videos/hello.mp4`
5. Repeat for ~20-50 common words

Or use the Python helper:
```bash
python sign_video_downloader.py --add hello --file /path/to/hello.mp4
python sign_video_downloader.py --list  # See what you have
```

### Option B: Download Multiple Videos

From a folder with video files:
```bash
python sign_video_downloader.py --import /path/to/videos/folder
```

### Option C: Download from YouTube

Install `yt-dlp`:
```bash
pip install yt-dlp
```

Then download videos:
```bash
# Single video
yt-dlp -f best[ext=mp4] https://www.youtube.com/watch?v=VIDEO_ID -o "hello.mp4"

# Move to correct folder
mv hello.mp4 static/signs/videos/

# Register with system
python sign_video_downloader.py --add hello --file static/signs/videos/hello.mp4
```

## Verify Setup

```bash
# List all registered videos
python sign_video_downloader.py --list

# Test API
curl -X POST http://localhost:5000/text-to-sign \
  -H "Content-Type: application/json" \
  -d '{"text":"hello"}'
```

Expected response shows video URLs:
```json
{
  "sign_sequence": [
    {
      "video_url": "/static/signs/videos/hello.mp4"
    }
  ]
}
```

## Test in Browser

1. Open http://localhost:5000
2. Type: "hello thank you please"
3. Click: "Translate Text"
4. **See**: Real human sign language videos playing in the Sign Output panel!

## Fallback: Placeholder Images

If you don't add real videos yet:
- System automatically falls back to PNG placeholders
- Shows text-based signs while you gather videos
- Smooth transition once videos are added

## Directory Structure

After setup, your folder should look like:
```
Sign_language_translator/
├── backend/
│   ├── app.py (← switched from app_v2.py)
│   ├── text_to_sign.py (← switched from text_to_sign_v2.py)
│   ├── sign_video_manager.py
│   └── ...
├── static/
│   └── signs/
│       ├── videos/  (← real human videos here)
│       │   ├── hello.mp4
│       │   ├── thank-you.mp4
│       │   ├── please.mp4
│       │   └── ... (more videos)
│       ├── videos_metadata.json (← auto-generated)
│       ├── (placeholder PNGs as fallback)
│       └── ...
├── SIGN_LANGUAGE_VIDEOS_GUIDE.md
├── sign_video_downloader.py
└── ...
```

## Troubleshooting

### "Video not playing"
- Check browser console (F12) for errors
- Verify file is MP4 format: `ffmpeg -i video.mov -c:v h264 output.mp4`
- Check file is in `static/signs/videos/` folder

### "Metadata not updating"
- Delete `static/signs/videos_metadata.json`
- Restart server
- System auto-recreates it

### "Can't find my videos"
- Filenames must match word list exactly
- Use: `python sign_video_downloader.py --list`
- Rename files if needed

## Comparison

| Aspect | Before | After |
|--------|--------|-------|
| Sign Display | PNG text images | Real human videos |
| Quality | ⭐ Text placeholder | ⭐⭐⭐⭐⭐ Professional ASL |
| Authenticity | Machine-generated | Actual sign language |
| User Experience | Learning-oriented | Immersive & authentic |
| Setup Time | 0 min | 5-30 min (adding videos) |
| Video Count | 0 | 10-1000+ (you choose) |

## Next Steps

1. Switch to `app_v2.py` ✅ (completed above)
2. Download 10-20 sample videos ✅ (see options above)
3. Register videos with system ✅ (use sign_video_downloader.py)
4. Test in browser ✅ (type → see real videos)
5. Expand video library gradually 📈 (more words = better coverage)

## Support

For help with:
- **ASL Videos**: See SIGN_LANGUAGE_VIDEOS_GUIDE.md
- **Video Download**: Check FFmpeg docs or yt-dlp docs
- **System Issues**: Check Flask logs in terminal

---

**Your sign language translator is now ready for real human videos!**

Start by downloading 5-10 common ASL videos and watch your system come to life.
