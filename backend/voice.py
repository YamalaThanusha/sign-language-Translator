import pyttsx3
import os
import uuid
import threading

def _generate_audio_file(text, output_path):
    # Initialize engine inside the thread to avoid COM-related issues on Windows
    # or general threading issues with pyttsx3
    try:
        engine = pyttsx3.init()
        # You can adjust properties like rate or volume here if needed
        # engine.setProperty('rate', 150)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
    except Exception as e:
        print(f"Error initializing pyttsx3: {e}")

def process_text_to_audio(text):
    """
    Converts a text string to an audio file and returns the web-accessible url.
    Uses pyttsx3 engine.
    """
    # Generate unique filename
    filename = f"audio_{uuid.uuid4().hex}.mp3"
    
    # Needs to be saved in the static folder to be accessible via URL
    static_folder = os.path.join(os.path.dirname(__file__), '..', 'static')
    audio_folder = os.path.join(static_folder, 'audio')
    
    # Ensure audio folder exists
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)
        
    output_path = os.path.join(audio_folder, filename)
    
    # Windows pyttsx3 needs to be run in its own thread block often when combined with Flask
    # to avoid freezing the main thread or causing COM context errors.
    t = threading.Thread(target=_generate_audio_file, args=(text, output_path))
    t.start()
    t.join()
    
    # Return path relative to static folder
    return f"/static/audio/{filename}"
