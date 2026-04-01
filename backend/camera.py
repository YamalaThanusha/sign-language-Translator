import cv2
import mediapipe as mp
import numpy as np
import os
import joblib

# Initialize mediapipe Hands globally to avoid reloading 
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,       # True since we're processing individual frames from API
    max_num_hands=1,
    min_detection_confidence=0.5
)

loaded_model = None

def load_gesture_model():
    global loaded_model
    if loaded_model is None:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'gesture_model.pkl')
        if os.path.exists(model_path):
            try:
                loaded_model = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading model: {e}")
                
def classify_gesture_ml(landmarks):
    load_gesture_model()
    
    if loaded_model is None:
        return None  # No model trained yet
        
    try:
        # Extract features (x, y) coordinates
        features = []
        for lm in landmarks:
            features.extend([lm.x, lm.y])
            
        prediction = loaded_model.predict([features])
        return prediction[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

def process_frame_for_sign(image_bytes):
    """
    Takes raw image bytes, converts to OpenCV format,
    runs Mediapipe hand detection, and classifies the gesture using trained ML model.
    Returns classified text or None.
    """
    # Decode bytes to image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None
        
    # Convert BGR to RGB for Mediapipe
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = hands.process(img_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            landmarks = hand_landmarks.landmark
            text = classify_gesture_ml(landmarks)
            if text:
                return text
                
    return None
