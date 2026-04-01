import speech_recognition as sr
import os

def process_audio_to_text(audio_file):
    """
    Takes a FileStorage object from Flask (an audio file uploaded from frontend),
    processes it through SpeechRecognition to text.
    """
    # Save the file temporarily
    temp_path = "temp_audio.wav"
    audio_file.save(temp_path)
    
    r = sr.Recognizer()
    text = ""
    try:
        with sr.AudioFile(temp_path) as source:
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.record(source)
            text = r.recognize_google(audio)
            print("Recognized Speech:", text)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        text = "Sorry, could not understand audio."
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        text = f"Speech recognition service error."
    except Exception as e:
        print(f"Error in speech recognition: {e}")
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
                
    return text
