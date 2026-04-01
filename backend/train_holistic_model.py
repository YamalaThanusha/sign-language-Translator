from pathlib import Path
from typing import Iterable, Optional

import cv2
import joblib
import mediapipe as mp
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


FACE_LANDMARKS = 468
POSE_LANDMARKS = 33
HAND_LANDMARKS = 21
SUPPORTED_EXTENSIONS = {".gif", ".mp4", ".webm", ".mov", ".avi", ".mkv", ".jpg", ".jpeg", ".png", ".bmp"}


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sanitize_label(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").strip().lower()


def extract_landmark_block(landmarks, count: int) -> list[float]:
    features: list[float] = []
    for idx in range(count):
        if landmarks is not None and idx < len(landmarks):
            lm = landmarks[idx]
            features.extend([float(lm.x), float(lm.y), float(lm.z)])
        else:
            features.extend([0.0, 0.0, 0.0])
    return features


def extract_holistic_features(results) -> list[float]:
    values: list[float] = []
    values.extend(
        extract_landmark_block(
            getattr(getattr(results, "face_landmarks", None), "landmark", None),
            FACE_LANDMARKS,
        )
    )
    values.extend(
        extract_landmark_block(
            getattr(getattr(results, "left_hand_landmarks", None), "landmark", None),
            HAND_LANDMARKS,
        )
    )
    values.extend(
        extract_landmark_block(
            getattr(getattr(results, "pose_landmarks", None), "landmark", None),
            POSE_LANDMARKS,
        )
    )
    values.extend(
        extract_landmark_block(
            getattr(getattr(results, "right_hand_landmarks", None), "landmark", None),
            HAND_LANDMARKS,
        )
    )
    return values


def iter_media_files(signs_dir: Path) -> Iterable[Path]:
    for p in signs_dir.iterdir():
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield p


def iter_dataset_images(dataset_dir: Path) -> Iterable[tuple[str, Path]]:
    if not dataset_dir.exists():
        return
    for class_dir in sorted(dataset_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        label = sanitize_label(class_dir.name)
        for image_path in sorted(class_dir.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield label, image_path


def extract_frames(media_path: Path, max_frames: int = 60, stride: int = 2) -> list[np.ndarray]:
    frames: list[np.ndarray] = []
    suffix = media_path.suffix.lower()

    if suffix in {".jpg", ".jpeg", ".png", ".bmp"}:
        img = cv2.imread(str(media_path))
        if img is not None:
            frames.append(img)
        return frames

    cap = cv2.VideoCapture(str(media_path))
    if not cap.isOpened():
        return frames

    frame_idx = 0
    try:
        while len(frames) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % stride == 0:
                frames.append(frame)
            frame_idx += 1
    finally:
        cap.release()

    return frames


def collect_training_data(signs_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    data: list[list[float]] = []
    labels: list[str] = []

    try:
        for media_file in iter_media_files(signs_dir):
            label = sanitize_label(media_file.stem)
            if label == "browser upload test":
                continue

            frames = extract_frames(media_file)
            if not frames:
                print(f"Skipping {media_file.name}: no readable frames")
                continue

            sample_count = 0
            for frame in frames:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(rgb)
                if not results:
                    continue

                has_any_landmark = any(
                    getattr(results, attr, None) is not None
                    for attr in ("left_hand_landmarks", "right_hand_landmarks", "pose_landmarks", "face_landmarks")
                )
                if not has_any_landmark:
                    continue

                features = extract_holistic_features(results)
                data.append(features)
                labels.append(label)
                sample_count += 1

                # Mirror augmentation improves webcam parity.
                flipped = cv2.flip(frame, 1)
                flipped_rgb = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)
                flipped_results = holistic.process(flipped_rgb)
                if flipped_results:
                    flipped_features = extract_holistic_features(flipped_results)
                    data.append(flipped_features)
                    labels.append(label)
                    sample_count += 1

            print(f"Collected {sample_count} samples for label '{label}' from {media_file.name}")
    finally:
        holistic.close()

    if not data:
        return np.array([]), np.array([])

    return np.array(data, dtype=np.float32), np.array(labels)


def collect_training_data_from_dataset(dataset_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    data: list[list[float]] = []
    labels: list[str] = []
    per_label_count: dict[str, int] = {}

    try:
        for label, image_path in iter_dataset_images(dataset_dir):
            img = cv2.imread(str(image_path))
            if img is None:
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)
            if not results:
                continue

            has_any_landmark = any(
                getattr(results, attr, None) is not None
                for attr in ("left_hand_landmarks", "right_hand_landmarks", "pose_landmarks", "face_landmarks")
            )
            if not has_any_landmark:
                continue

            features = extract_holistic_features(results)
            data.append(features)
            labels.append(label)
            per_label_count[label] = per_label_count.get(label, 0) + 1

            flipped = cv2.flip(img, 1)
            flipped_rgb = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)
            flipped_results = holistic.process(flipped_rgb)
            if flipped_results:
                flipped_features = extract_holistic_features(flipped_results)
                data.append(flipped_features)
                labels.append(label)
                per_label_count[label] = per_label_count.get(label, 0) + 1
    finally:
        holistic.close()

    for label in sorted(per_label_count.keys()):
        print(f"Collected {per_label_count[label]} samples for label '{label}' from dataset_holistic")

    if not data:
        return np.array([]), np.array([])

    return np.array(data, dtype=np.float32), np.array(labels)


def train_holistic_model() -> Optional[Path]:
    root = project_root()
    holistic_dataset_dir = root / "dataset_holistic"
    signs_dir = root / "static" / "signs"
    model_dir = root / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    X, y = collect_training_data_from_dataset(holistic_dataset_dir)
    if X.size == 0 or y.size == 0:
        print("No valid webcam samples found in dataset_holistic. Falling back to static/signs media files.")
        X, y = collect_training_data(signs_dir)

    if X.size == 0 or y.size == 0:
        print("No Holistic samples could be extracted from dataset_holistic or static/signs.")
        return None

    unique_labels = sorted(set(y.tolist()))
    print(f"Labels ({len(unique_labels)}): {unique_labels}")
    print(f"Training samples: {len(X)}; feature shape: {X.shape[1]}")

    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    if len(unique_labels) > 1 and len(X) > 20:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"Validation accuracy: {acc * 100:.2f}%")
    else:
        clf.fit(X, y)
        print("Trained on all samples (insufficient size/class balance for validation split).")

    model_path = model_dir / "gesture_model.pkl"
    joblib.dump(clf, model_path)
    print(f"Saved Holistic model to: {model_path}")
    print(f"Model expects n_features_in_={getattr(clf, 'n_features_in_', None)}")
    return model_path


if __name__ == "__main__":
    train_holistic_model()
