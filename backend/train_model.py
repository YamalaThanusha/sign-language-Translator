import os
import cv2
import mediapipe as mp
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def extract_landmarks(image_path, hands):
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append(lm.x)
                landmarks.append(lm.y)
                # optionally include z: landmarks.append(lm.z)
            return landmarks
    return None

def train_model():
    dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'dataset')
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
    
    os.makedirs(model_dir, exist_ok=True)
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.5
    )
    
    data = []
    labels = []
    
    classes = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]
    print(f"Found classes: {classes}")
    
    for class_name in classes:
        class_dir = os.path.join(dataset_dir, class_name)
        images = os.listdir(class_dir)
        
        for img_name in images:
            img_path = os.path.join(class_dir, img_name)
            if not img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            landmarks = extract_landmarks(img_path, hands)
            if landmarks:
                data.append(landmarks)
                labels.append(class_name)
                
    if not data:
        print("No valid data found to train on. Please collect data first using backend/collect_data.py")
        
        # Create a dummy model to prevent errors if no data exists yet
        print("Creating a dummy model for now so the app can start...")
        dummy_clf = RandomForestClassifier()
        # Train on 0s
        dummy_X = [[0.0] * 42 for _ in range(4)]
        dummy_y = ['sign_a', 'sign_b', 'sign_c', 'sign_d']
        dummy_clf.fit(dummy_X, dummy_y)
        model_path = os.path.join(model_dir, 'gesture_model.pkl')
        joblib.dump(dummy_clf, model_path)
        print(f"Dummy model saved to {model_path}")
        return
        
    X = np.array(data)
    y = np.array(labels)
    
    print(f"Training on {len(X)} samples...")
    
    if len(np.unique(y)) > 1 and len(X) > 1:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"Model trained! Accuracy on validation set: {acc * 100:.2f}%")
        
    else:
        # Not enough classes for split, train on all
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, y)
        print("Model trained on all data (not enough samples for validation split).")
        
    model_path = os.path.join(model_dir, 'gesture_model.pkl')
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
