"""
Sign Language Video Management System

This module handles:
1. Downloading real sign language videos from free public sources
2. Organizing videos by word/gloss
3. Managing video metadata
4. Converting videos to web-friendly formats
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, List

SIGNS_DIR = Path(__file__).parent / 'static' / 'signs'
VIDEOS_DIR = SIGNS_DIR / 'videos'
METADATA_FILE = SIGNS_DIR / 'videos_metadata.json'

def ensure_directories():
    """Create necessary directories."""
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directories ready at {VIDEOS_DIR}")

def load_metadata() -> Dict:
    """Load existing video metadata."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"videos": {}, "sources": []}

def save_metadata(metadata: Dict):
    """Save video metadata."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def add_video_file(word: str, video_path: str, gloss: str = "", source: str = "manual"):
    """
    Register a video file in the system.
    
    Args:
        word: English word (e.g., 'hello')
        video_path: Path to existing video file
        gloss: ASL gloss (e.g., 'HELLO')
        source: Where the video came from
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"✗ Video file not found: {video_path}")
        return False
    
    # Copy video to videos directory
    dest_filename = f"{word}.{video_path.suffix.lstrip('.')}"
    dest_path = VIDEOS_DIR / dest_filename
    
    # Copy the file
    import shutil
    shutil.copy2(str(video_path), str(dest_path))
    
    # Update metadata
    metadata = load_metadata()
    metadata["videos"][word] = {
        "word": word,
        "gloss": gloss or word.upper(),
        "file": dest_filename,
        "format": video_path.suffix.lstrip('.'),
        "source": source,
        "size_bytes": dest_path.stat().st_size,
    }
    
    if source not in metadata.get("sources", []):
        metadata["sources"] = metadata.get("sources", []) + [source]
    
    save_metadata(metadata)
    print(f"✓ Added video: {word} ({dest_filename})")
    return True

def list_available_videos() -> Dict:
    """List all available sign language videos."""
    metadata = load_metadata()
    videos = metadata.get("videos", {})
    
    if not videos:
        print("No videos registered yet.")
        return {}
    
    print("\nAvailable Sign Language Videos:")
    print("=" * 60)
    for word, info in sorted(videos.items()):
        size_mb = info.get('size_bytes', 0) / (1024 * 1024)
        print(f"  {word:15} → {info['gloss']:20} ({info['file']}) [{size_mb:.1f}MB]")
    print("=" * 60)
    print(f"Total: {len(videos)} videos\n")
    
    return videos

def validate_video_format(video_path: str) -> bool:
    """Check if video is in a web-friendly format."""
    supported = {'.mp4', '.webm', '.avi', '.mov'}
    ext = Path(video_path).suffix.lower()
    return ext in supported

def convert_to_mp4(input_path: str, output_path: Optional[str] = None) -> bool:
    """
    Convert video to MP4 format using ffmpeg.
    Requires ffmpeg to be installed: pip install ffmpeg-python
    """
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"✗ Input file not found: {input_path}")
        return False
    
    if output_path is None:
        output_path = input_path.with_suffix('.mp4')
    
    output_path = Path(output_path)
    
    try:
        # Try using ffmpeg command line
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✓ Converted to MP4: {output_path}")
            return True
        else:
            print(f"✗ FFmpeg error: {result.stderr.decode()}")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg not found. Install it: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False

def import_video_batch(source_dir: str):
    """
    Import multiple videos from a directory.
    Expected structure: {source_dir}/{word}/{video_file}
    """
    source_dir = Path(source_dir)
    
    if not source_dir.exists():
        print(f"✗ Source directory not found: {source_dir}")
        return
    
    count = 0
    for word_dir in source_dir.iterdir():
        if not word_dir.is_dir():
            continue
        
        word = word_dir.name.lower()
        
        # Find first video file
        for video_file in word_dir.glob('*'):
            if video_file.is_file() and validate_video_format(str(video_file)):
                if add_video_file(word, str(video_file), source=source_dir.name):
                    count += 1
                break
    
    print(f"\n✓ Imported {count} videos from {source_dir.name}")

def get_video_url(word: str) -> Optional[str]:
    """Get the Flask URL for a sign language video."""
    metadata = load_metadata()
    videos = metadata.get("videos", {})
    
    if word in videos:
        filename = videos[word].get('file')
        return f"/static/signs/videos/{filename}"
    
    return None

if __name__ == "__main__":
    ensure_directories()
    list_available_videos()
    
    print("\nUsage Examples:")
    print("=" * 60)
    print("1. Add a single video:")
    print("   from sign_video_manager import add_video_file")
    print("   add_video_file('hello', '/path/to/hello.mp4', 'HELLO')")
    print()
    print("2. Import batch of videos:")
    print("   from sign_video_manager import import_video_batch")
    print("   import_video_batch('/path/to/video_dataset')")
    print()
    print("3. Convert video to MP4:")
    print("   from sign_video_manager import convert_to_mp4")
    print("   convert_to_mp4('video.mov', 'video.mp4')")
    print("=" * 60)
