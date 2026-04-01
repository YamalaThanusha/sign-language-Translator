#!/usr/bin/env python3
"""
Quick test script for the Sign Language Video system.

Tests:
1. Video manager functionality
2. API endpoints
3. Metadata handling
"""

import os
import sys
import json
from pathlib import Path
import urllib.request
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from sign_video_manager import ensure_directories, list_available_videos, load_metadata


def test_directories():
    """Test that directories are set up correctly."""
    print("\n" + "="*60)
    print("TEST 1: Directory Structure")
    print("="*60)
    
    ensure_directories()
    
    required_dirs = [
        Path(__file__).parent / 'static' / 'signs',
        Path(__file__).parent / 'static' / 'signs' / 'videos',
    ]
    
    for d in required_dirs:
        if d.exists():
            print(f"✅ {d.relative_to(Path(__file__).parent)}")
        else:
            print(f"❌ {d.relative_to(Path(__file__).parent)} - NOT FOUND")
            return False
    
    return True


def test_metadata():
    """Test metadata loading and saving."""
    print("\n" + "="*60)
    print("TEST 2: Metadata System")
    print("="*60)
    
    try:
        metadata = load_metadata()
        print(f"✅ Metadata loaded")
        print(f"   Videos registered: {len(metadata.get('videos', {}))}")
        print(f"   Sources: {metadata.get('sources', [])}")
        return True
    except Exception as e:
        print(f"❌ Metadata error: {e}")
        return False


def test_api_endpoint():
    """Test the Flask API endpoint."""
    print("\n" + "="*60)
    print("TEST 3: API Endpoint (/text-to-sign)")
    print("="*60)
    
    try:
        import json
        import urllib.request
        
        # Prepare request
        url = "http://localhost:5000/text-to-sign"
        data = json.dumps({"text": "hello thank you"}).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        # Send request
        print("Sending: {'text': 'hello thank you'}")
        
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Check response
        if result.get('success'):
            print(f"✅ API responded successfully")
            print(f"   Gloss: {result.get('gloss_line')}")
            
            # Check for videos in response
            signs_with_videos = [s for s in result.get('sign_sequence', []) 
                                if s.get('video_url')]
            signs_total = len(result.get('sign_sequence', []))
            
            print(f"   Signs found: {signs_total}")
            print(f"   Signs with videos: {len(signs_with_videos)}")
            
            if signs_with_videos:
                for sign in signs_with_videos:
                    print(f"     • {sign.get('gloss')} → {sign.get('video_url')}")
            
            return True
        else:
            print(f"❌ API error: {result.get('error')}")
            return False
            
    except urllib.error.URLError as e:
        print(f"❌ Cannot connect to Flask server at http://localhost:5000")
        print(f"   {e}")
        print(f"   Make sure to run: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_static_files():
    """Test that static files are being served."""
    print("\n" + "="*60)
    print("TEST 4: Static File Serving")
    print("="*60)
    
    try:
        metadata = load_metadata()
        videos = metadata.get('videos', {})
        
        if not videos:
            print("⚠️  No videos registered yet")
            print("   Use: python sign_video_downloader.py --add hello --file path/to/hello.mp4")
            return True
        
        # Test first available video
        first_word = list(videos.keys())[0]
        first_video = videos[first_word]
        video_url = f"/static/signs/videos/{first_video['file']}"
        full_url = f"http://localhost:5000{video_url}"
        
        print(f"Testing: {video_url}")
        
        request = urllib.request.Request(full_url, method='HEAD')
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status == 200:
                size_mb = int(response.headers.get('Content-Length', 0)) / (1024*1024)
                print(f"✅ Static file served correctly")
                print(f"   Size: {size_mb:.1f}MB")
                return True
            else:
                print(f"❌ Unexpected status: {response.status}")
                return False
                
    except urllib.error.URLError:
        print(f"⚠️  Flask server not running")
        return None  # Not a failure, just not ready yet
    except Exception as e:
        print(f"❌ Static file test failed: {e}")
        return False


def test_video_files():
    """Check for actual video files."""
    print("\n" + "="*60)
    print("TEST 5: Video Files")
    print("="*60)
    
    videos_dir = Path(__file__).parent / 'static' / 'signs' / 'videos'
    
    if not videos_dir.exists():
        print(f"⚠️  Videos directory not created yet: {videos_dir}")
        return True
    
    video_files = list(videos_dir.glob('*'))
    video_count = len([f for f in video_files if f.is_file()])
    
    if video_count == 0:
        print(f"⚠️  No video files found in {videos_dir}")
        print(f"   Start adding videos with:")
        print(f"   python sign_video_downloader.py --add hello --file /path/to/hello.mp4")
        return True
    
    print(f"✅ Found {video_count} video files:")
    for f in sorted(video_files)[:10]:
        if f.is_file():
            size_mb = f.stat().st_size / (1024*1024)
            print(f"   • {f.name} ({size_mb:.1f}MB)")
    
    if video_count > 10:
        print(f"   ... and {video_count - 10} more")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Sign Language Video Translator - Test Suite")
    print("="*60)
    
    results = {
        "Directories": test_directories(),
        "Metadata": test_metadata(),
        "Video Files": test_video_files(),
        "API Endpoint": test_api_endpoint(),
        "Static Files": test_static_files(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            symbol = "✅"
        elif result is False:
            symbol = "❌"
        else:
            symbol = "⚠️"
        print(f"{symbol} {test_name}")
    
    print("\n" + "-"*60)
    print(f"Passed: {passed} | Failed: {failed} | Skipped/Warning: {skipped}")
    print("-"*60)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1
    elif skipped > 0:
        print("\n⚠️  Some tests were skipped (Flask may not be running).")
        print("   To run full tests: python app.py (in another terminal)")
        return 0
    else:
        print("\n✅ All tests passed! Your system is ready to use.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
