#!/usr/bin/env python3
"""
Helper script to download and manage real sign language videos.

Usage:
  python sign_video_downloader.py --help
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from sign_video_manager import add_video_file, import_video_batch, list_available_videos


def ensure_videos_dir():
    """Ensure videos directory exists."""
    videos_dir = Path(__file__).parent / 'static' / 'signs' / 'videos'
    videos_dir.mkdir(parents=True, exist_ok=True)
    return videos_dir


def download_from_urls(urls: List[str], word: str):
    """Download videos from URLs (requires youtube-dl)."""
    try:
        import yt_dlp
    except ImportError:
        print("❌ yt-dlp not installed. Install with: pip install yt-dlp")
        return False
    
    videos_dir = ensure_videos_dir()
    
    for url in urls:
        try:
            with yt_dlp.YoutubeDL({
                'format': 'best[ext=mp4]',
                'outtmpl': str(videos_dir / f'{word}%(ext)s'),
                'quiet': False,
                'no_warnings': False,
            }) as ydl:
                print(f"📥 Downloading: {url}")
                ydl.download([url])
                print(f"✅ Downloaded: {word}.mp4")
                
                # Register in system
                add_video_file(word, str(videos_dir / f'{word}.mp4'), source='youtube')
                return True
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            return False


def add_local_video(word: str, file_path: str, gloss: Optional[str] = None):
    """Add a local video file to the system."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    if add_video_file(word, file_path, gloss=gloss or word.upper(), source='local'):
        print(f"✅ Added video for: {word}")
        return True
    return False


def batch_import_from_folder(folder_path: str):
    """Import all videos from a folder."""
    if not os.path.isdir(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return False
    
    print(f"📂 Importing videos from: {folder_path}")
    import_video_batch(folder_path)
    return True


def create_sample_metadata():
    """Create a sample videos_metadata.json for reference."""
    sample_metadata = {
        "videos": {
            "hello": {
                "word": "hello",
                "gloss": "HELLO",
                "file": "hello.mp4",
                "format": "mp4",
                "source": "signasl",
                "size_bytes": 1024000
            },
            "thank-you": {
                "word": "thank-you",
                "gloss": "THANK-YOU",
                "file": "thank-you.mp4",
                "format": "mp4",
                "source": "signasl",
                "size_bytes": 1536000
            },
            "please": {
                "word": "please",
                "gloss": "PLEASE",
                "file": "please.mp4",
                "format": "mp4",
                "source": "handspeak",
                "size_bytes": 896000
            }
        },
        "sources": [
            "signasl",
            "handspeak",
            "asl_connect",
            "youtube",
            "local"
        ],
        "total_videos": 3,
        "total_size_mb": 3.5,
        "last_updated": "2024-03-30"
    }
    
    metadata_path = Path(__file__).parent / 'static' / 'signs' / 'videos_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(sample_metadata, f, indent=2)
    
    print(f"✅ Created sample metadata: {metadata_path}")
    print("\nReplace 'hello.mp4' with your actual video files.")


def cli_main():
    """Command-line interface for video management."""
    parser = argparse.ArgumentParser(
        description='Sign Language Video Manager',
        epilog='''
Examples:
  # Add single video
  python sign_video_downloader.py --add hello /path/to/hello.mp4
  
  # Import all videos from folder
  python sign_video_downloader.py --import /path/to/videos
  
  # List all videos
  python sign_video_downloader.py --list
  
  # Create sample metadata
  python sign_video_downloader.py --create-sample
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--add', type=str, metavar='WORD', 
                       help='Add a video file (use with --file)')
    parser.add_argument('--file', type=str, metavar='PATH',
                       help='Path to video file (use with --add)')
    parser.add_argument('--gloss', type=str, metavar='GLOSS',
                       help='ASL gloss for the sign (optional)')
    parser.add_argument('--import', type=str, metavar='FOLDER', dest='import_folder',
                       help='Import all videos from folder')
    parser.add_argument('--list', action='store_true',
                       help='List all available videos')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample metadata.json')
    parser.add_argument('--ensure-dir', action='store_true',
                       help='Ensure videos directory exists')
    
    args = parser.parse_args()
    
    if args.ensure_dir:
        videos_dir = ensure_videos_dir()
        print(f"✅ Videos directory ready: {videos_dir}")
        return 0
    
    if args.list:
        list_available_videos()
        return 0
    
    if args.create_sample:
        create_sample_metadata()
        return 0
    
    if args.add:
        if not args.file:
            print("❌ Error: --add requires --file")
            return 1
        if add_local_video(args.add, args.file, args.gloss):
            return 0
        return 1
    
    if args.import_folder:
        if batch_import_from_folder(args.import_folder):
            return 0
        return 1
    
    if not any([args.add, args.import_folder, args.list, args.create_sample, args.ensure_dir]):
        parser.print_help()
        return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(cli_main())
