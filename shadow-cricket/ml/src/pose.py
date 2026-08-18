import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Dict, Any

mp_pose = mp.solutions.pose

class PoseExtractor:
    def __init__(self, static_image_mode: bool = True, model_complexity: int = 2, min_detection_confidence: float = 0.5):
        self.pose = mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence
        )

    def extract_landmarks(self, image_bytes: bytes) -> Optional[List[Dict[str, float]]]:
        # Decode the image bytes to a numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return None

        # Convert BGR to RGB as mediapipe expects RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        results = self.pose.process(img_rgb)

        if not results.pose_landmarks:
            return None

        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.append({
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility
            })

        return landmarks

    def close(self):
        self.pose.close()

pose_extractor = PoseExtractor()
