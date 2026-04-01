from __future__ import annotations

from collections import deque
import os
from typing import Optional, Sequence

import cv2
import joblib
import mediapipe as mp
import numpy as np


class SignModel:
    """
    Runtime sign recognizer using MediaPipe Holistic landmarks + sklearn model.

    This module centralizes the sign prediction logic so backend routes can
    import it directly instead of depending on notebook code.
    """

    FACE_LANDMARKS = 468
    POSE_LANDMARKS = 33
    HAND_LANDMARKS = 21
    MIN_CONFIDENCE = 0.35
    STABILITY_WINDOW = 2
    MIN_VOTES = 2

    def __init__(self) -> None:
        self._mp_holistic = mp.solutions.holistic
        self._holistic = self._mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            refine_face_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._loaded_model = None
        self._expected_features = None
        self._recent_predictions: deque[str] = deque(maxlen=self.STABILITY_WINDOW)

    def _model_path(self) -> str:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        return os.path.join(project_root, "model", "gesture_model.pkl")

    def _load_model(self):
        if self._loaded_model is not None:
            return self._loaded_model

        model_path = self._model_path()
        if not os.path.exists(model_path):
            return None

        try:
            self._loaded_model = joblib.load(model_path)
            self._expected_features = getattr(self._loaded_model, "n_features_in_", None)
        except Exception as e:
            print(f"Error loading gesture model: {e}")
            self._loaded_model = None
            self._expected_features = None

        return self._loaded_model

    def _extract_landmark_block(
        self,
        landmarks: Optional[Sequence],
        count: int,
        include_z: bool = True,
    ) -> list[float]:
        features: list[float] = []
        for index in range(count):
            if landmarks is not None and index < len(landmarks):
                landmark = landmarks[index]
                if include_z:
                    features.extend([float(landmark.x), float(landmark.y), float(landmark.z)])
                else:
                    features.extend([float(landmark.x), float(landmark.y)])
            else:
                if include_z:
                    features.extend([0.0, 0.0, 0.0])
                else:
                    features.extend([0.0, 0.0])
        return features

    def _extract_full_holistic_features(self, results, include_frame: bool = False) -> list[float]:
        features: list[float] = [0.0] if include_frame else []
        features.extend(self._extract_landmark_block(getattr(getattr(results, "face_landmarks", None), "landmark", None), self.FACE_LANDMARKS))
        features.extend(self._extract_landmark_block(getattr(getattr(results, "left_hand_landmarks", None), "landmark", None), self.HAND_LANDMARKS))
        features.extend(self._extract_landmark_block(getattr(getattr(results, "pose_landmarks", None), "landmark", None), self.POSE_LANDMARKS))
        features.extend(self._extract_landmark_block(getattr(getattr(results, "right_hand_landmarks", None), "landmark", None), self.HAND_LANDMARKS))
        return features

    def _extract_hand_features(self, results) -> Optional[list[float]]:
        right_hand = getattr(getattr(results, "right_hand_landmarks", None), "landmark", None)
        left_hand = getattr(getattr(results, "left_hand_landmarks", None), "landmark", None)

        if right_hand is not None:
            return self._extract_landmark_block(right_hand, self.HAND_LANDMARKS, include_z=False)
        if left_hand is not None:
            return self._extract_landmark_block(left_hand, self.HAND_LANDMARKS, include_z=False)

        return None

    def _predict_with_features(self, features: list[float]) -> Optional[str]:
        try:
            probabilities = None
            if hasattr(self._loaded_model, "predict_proba"):
                probabilities = self._loaded_model.predict_proba([features])[0]

            prediction = self._loaded_model.predict([features])
            if prediction is None or len(prediction) == 0:
                return None

            label = str(prediction[0])

            if probabilities is not None and len(probabilities) > 0:
                confidence = float(np.max(probabilities))
                if confidence < self.MIN_CONFIDENCE:
                    return None

            return label
        except Exception as e:
            print(f"Prediction error: {e}")

        return None

    def _stabilize_prediction(self, label: Optional[str]) -> Optional[str]:
        if not label:
            self._recent_predictions.clear()
            return None

        self._recent_predictions.append(label)
        if len(self._recent_predictions) < self.STABILITY_WINDOW:
            return None

        votes = sum(1 for item in self._recent_predictions if item == label)
        if votes >= self.MIN_VOTES:
            return label

        return None

    def _decode_image(self, image_bytes: bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def _predict_from_rgb_image(self, img_rgb) -> Optional[str]:
        results = self._holistic.process(img_rgb)
        if not results:
            return None

        if self._expected_features in (1629, 1630):
            features = self._extract_full_holistic_features(
                results,
                include_frame=self._expected_features == 1630,
            )
            return self._predict_with_features(features)

        hand_features = self._extract_hand_features(results)
        if hand_features is not None and self._expected_features in (None, 42):
            return self._predict_with_features(hand_features)

        if self._expected_features == 42:
            right_hand_landmarks = getattr(getattr(results, "right_hand_landmarks", None), "landmark", None)
            if right_hand_landmarks is None:
                right_hand_landmarks = getattr(getattr(results, "left_hand_landmarks", None), "landmark", None)
            if right_hand_landmarks is None:
                return None
            right_hand_only = self._extract_landmark_block(
                right_hand_landmarks,
                self.HAND_LANDMARKS,
                include_z=False,
            )
            return self._predict_with_features(right_hand_only)

        return None

    def predict_from_image_bytes(self, image_bytes: bytes) -> Optional[str]:
        model = self._load_model()
        if model is None:
            return None

        img = self._decode_image(image_bytes)
        if img is None:
            return None

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Try the original frame first, then a mirrored frame.
        # Webcams are often displayed mirrored in browser UIs, and this fallback
        # makes recognition more tolerant of that setup.
        raw_prediction = None
        for candidate in (img_rgb, cv2.flip(img_rgb, 1)):
            prediction = self._predict_from_rgb_image(candidate)
            if prediction:
                raw_prediction = prediction
                break

        return self._stabilize_prediction(raw_prediction)


# Shared singleton for backend request handlers.
sign_model = SignModel()
