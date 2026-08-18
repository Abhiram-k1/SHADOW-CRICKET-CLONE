import math
from typing import List, Dict, Tuple, Any

class ScoringEngine:
    """
    Computes deterministic scores based on MediaPipe landmarks.
    Power is returned as a 'proxy', strictly an estimation based on posture.
    """

    def __init__(self):
        # MediaPipe Landmark IDs
        self.NOSE = 0
        self.L_SHOULDER = 11
        self.R_SHOULDER = 12
        self.L_HIP = 23
        self.R_HIP = 24
        self.L_KNEE = 25
        self.R_KNEE = 26
        self.L_ANKLE = 27
        self.R_ANKLE = 28

    def _get_distance(self, lm1: Dict, lm2: Dict) -> float:
        return math.sqrt((lm1['x'] - lm2['x'])**2 + (lm1['y'] - lm2['y'])**2)

    def _get_angle(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        # Angle between p1, p2 (vertex), and p3
        a = self._get_distance(p1, p2)
        b = self._get_distance(p2, p3)
        c = self._get_distance(p1, p3)
        if a == 0 or b == 0:
            return 0.0
        # Law of cosines
        val = (a**2 + b**2 - c**2) / (2 * a * b)
        val = max(min(val, 1.0), -1.0)
        return math.degrees(math.acos(val))

    def compute_balance(self, landmarks: List[Dict]) -> float:
        if not landmarks or len(landmarks) < 33:
            return 0.0

        l_ankle = landmarks[self.L_ANKLE]
        r_ankle = landmarks[self.R_ANKLE]
        nose = landmarks[self.NOSE]

        # Simple center of mass proxy: nose x relative to ankles x
        base_center_x = (l_ankle['x'] + r_ankle['x']) / 2.0
        base_width = abs(l_ankle['x'] - r_ankle['x']) + 1e-6

        deviation = abs(nose['x'] - base_center_x) / base_width
        score = max(0.0, 100.0 - (deviation * 50.0))
        return min(100.0, score)

    def compute_alignment(self, landmarks: List[Dict]) -> float:
        if not landmarks or len(landmarks) < 33:
            return 0.0

        l_shoulder = landmarks[self.L_SHOULDER]
        r_shoulder = landmarks[self.R_SHOULDER]
        l_hip = landmarks[self.L_HIP]
        r_hip = landmarks[self.R_HIP]

        # Proxy alignment: difference between shoulder tilt and hip tilt
        shoulder_tilt = abs(l_shoulder['y'] - r_shoulder['y'])
        hip_tilt = abs(l_hip['y'] - r_hip['y'])

        diff = abs(shoulder_tilt - hip_tilt)
        score = max(0.0, 100.0 - (diff * 200.0))
        return min(100.0, score)

    def compute_stance(self, landmarks: List[Dict]) -> float:
        if not landmarks or len(landmarks) < 33:
            return 0.0

        # Proxy: Knee flexion angle (we'll just use the right knee as an example)
        angle = self._get_angle(landmarks[self.R_HIP], landmarks[self.R_KNEE], landmarks[self.R_ANKLE])

        # Ideal stance might have a slight bend, say 150-170 degrees
        target_angle = 160.0
        diff = abs(angle - target_angle)

        score = max(0.0, 100.0 - (diff * 1.5))
        return min(100.0, score)

    def compute_power_proxy(self, landmarks: List[Dict], confidence: float) -> float:
        if not landmarks or len(landmarks) < 33:
            return 0.0

        # Power is a blend of model confidence and hip-shoulder separation (rotation)
        # Using simple x distance between left hip and left shoulder as a naive rotation proxy
        sep = abs(landmarks[self.L_HIP]['x'] - landmarks[self.L_SHOULDER]['x'])

        # Scale sep to a 0-100 range roughly
        sep_score = min(100.0, sep * 500.0)

        proxy = (sep_score * 0.4) + (confidence * 100.0 * 0.6)
        return min(100.0, proxy)

    def get_all_scores(self, landmarks: List[Dict], confidence: float = 0.8) -> Dict[str, float]:
        return {
            "balance": round(self.compute_balance(landmarks), 1),
            "alignment": round(self.compute_alignment(landmarks), 1),
            "stance": round(self.compute_stance(landmarks), 1),
            "power_proxy": round(self.compute_power_proxy(landmarks, confidence), 1)
        }

class RecommendationEngine:
    def __init__(self):
        # Category rules: Threshold -> Penalty Weight -> Template Text -> Category
        self.rules = [
            {"metric": "balance", "threshold": 75.0, "weight": 3, "text": "Keep your head more stable over your base.", "category": "Balance"},
            {"metric": "alignment", "threshold": 80.0, "weight": 2, "text": "Ensure your shoulders and hips are aligned towards the ball.", "category": "Alignment"},
            {"metric": "stance", "threshold": 70.0, "weight": 1, "text": "Maintain a slight bend in your knees for a strong base.", "category": "Stance"},
            {"metric": "power_proxy", "threshold": 60.0, "weight": 1, "text": "Focus on hip rotation to generate more bat speed.", "category": "Power"}
        ]

    def generate_recommendations(self, scores: Dict[str, float], limit: int = 3) -> List[Dict[str, Any]]:
        candidates = []

        for rule in self.rules:
            val = scores.get(rule["metric"], 100.0)
            if val < rule["threshold"]:
                diff = rule["threshold"] - val
                # Rank by (how far below) * weight
                score_rank = diff * rule["weight"]
                candidates.append({
                    "priority": int(score_rank),
                    "text": rule["text"],
                    "category": rule["category"]
                })

        # Sort descending by priority
        candidates = sorted(candidates, key=lambda x: x["priority"], reverse=True)
        return candidates[:limit]

scoring_engine = ScoringEngine()
recommendation_engine = RecommendationEngine()
