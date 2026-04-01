import cv2
import os
import mediapipe as mp
import time

def collect_data(num_samples_per_class=50):
    dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'dataset')
    # Generic class labels — rename folders to your gesture names when collecting
    classes = ['sign_a', 'sign_b', 'sign_c', 'sign_d']
    
    for class_name in classes:
        os.makedirs(os.path.join(dataset_dir, class_name), exist_ok=True)
        
    cap = cv2.VideoCapture(0)
    
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5
    )

    print("Data collection will begin shortly...")
    
    for class_name in classes:
        print(f"\n--- Preparing to collect data for class: '{class_name}' ---")
        print("Press 's' to start capturing when ready.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
                
            cv2.putText(frame, f"Ready for: {class_name}. Press 's' to start.", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Data Collection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break
                
        time.sleep(1) # short pause
        
        count = 0
        while count < num_samples_per_class:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Save image
                    img_path = os.path.join(dataset_dir, class_name, f"img_{int(time.time()*1000)}.jpg")
                    cv2.imwrite(img_path, frame)
                    count += 1
                    print(f"Captured {count}/{num_samples_per_class} for {class_name}")
                    
                    time.sleep(0.1) # Small delay to avoid identical frames
                    
            cv2.putText(frame, f"Collecting: {class_name} ({count}/{num_samples_per_class})", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow('Data Collection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                 print("Data collection interrupted.")
                 cap.release()
                 cv2.destroyAllWindows()
                 return
                 
    cap.release()
    cv2.destroyAllWindows()
    print("\nData collection complete!")

if __name__ == "__main__":
    collect_data()
