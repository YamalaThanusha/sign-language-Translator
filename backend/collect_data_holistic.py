import argparse
import os
import time
from pathlib import Path

import cv2
import mediapipe as mp


DEFAULT_CLASSES = [
    "hello",
    "thankyou",
    "yes",
    "no",
    "good morning",
    "good evening",
    "what",
    "tomorrow",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Collect Holistic sign samples from webcam.")
    parser.add_argument(
        "--classes",
        type=str,
        default=",".join(DEFAULT_CLASSES),
        help="Comma-separated sign labels.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=80,
        help="Samples per class.",
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=2,
        help="Seconds before capture starts for each class.",
    )
    return parser.parse_args()


def slugify(label: str) -> str:
    return "_".join(label.strip().lower().split())


def collect_data(classes: list[str], samples_per_class: int, countdown: int):
    root = Path(__file__).resolve().parent.parent
    dataset_dir = root / "dataset_holistic"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    for c in classes:
        (dataset_dir / slugify(c)).mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to open webcam.")
        return

    mp_holistic = mp.solutions.holistic
    mp_draw = mp.solutions.drawing_utils
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    print("Press 's' to start each class. Press 'q' anytime to quit.")

    try:
        for label in classes:
            class_dir = dataset_dir / slugify(label)
            print(f"\nPreparing class: {label}")

            while True:
                ok, frame = cap.read()
                if not ok:
                    continue

                cv2.putText(frame, f"Ready: {label}. Press 's'", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow("Holistic Data Collection", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    return
                if key == ord("s"):
                    break

            for t in range(countdown, 0, -1):
                ok, frame = cap.read()
                if not ok:
                    continue
                cv2.putText(frame, f"{label} starts in {t}", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
                cv2.imshow("Holistic Data Collection", frame)
                cv2.waitKey(500)

            captured = 0
            while captured < samples_per_class:
                ok, frame = cap.read()
                if not ok:
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(rgb)

                has_landmarks = any(
                    getattr(results, attr, None) is not None
                    for attr in ("left_hand_landmarks", "right_hand_landmarks", "pose_landmarks")
                )

                if has_landmarks:
                    if results.left_hand_landmarks:
                        mp_draw.draw_landmarks(frame, results.left_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    if results.right_hand_landmarks:
                        mp_draw.draw_landmarks(frame, results.right_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    if results.pose_landmarks:
                        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)

                    ts = int(time.time() * 1000)
                    path = class_dir / f"img_{ts}.jpg"
                    cv2.imwrite(str(path), frame)
                    captured += 1
                    time.sleep(0.06)

                cv2.putText(frame, f"{label}: {captured}/{samples_per_class}", (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Holistic Data Collection", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    return

    finally:
        holistic.close()
        cap.release()
        cv2.destroyAllWindows()


def main():
    args = parse_args()
    classes = [c.strip() for c in args.classes.split(",") if c.strip()]
    if not classes:
        classes = DEFAULT_CLASSES

    collect_data(classes, args.samples, args.countdown)


if __name__ == "__main__":
    main()
