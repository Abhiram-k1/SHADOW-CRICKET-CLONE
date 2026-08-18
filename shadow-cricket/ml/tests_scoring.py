import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.src.scoring import scoring_engine, recommendation_engine

def test_scoring_engines():
    # Create a perfect dummy landmark set
    dummy_landmarks = [{'x': 0.5, 'y': 0.5, 'z': 0, 'visibility': 1.0} for _ in range(33)]

    # Adjust a few to represent an imperfect, off-balance posture
    dummy_landmarks[scoring_engine.L_ANKLE] = {'x': 0.4, 'y': 0.9}
    dummy_landmarks[scoring_engine.R_ANKLE] = {'x': 0.6, 'y': 0.9}
    dummy_landmarks[scoring_engine.NOSE] = {'x': 0.8, 'y': 0.1} # Head leaning far right

    dummy_landmarks[scoring_engine.R_HIP] = {'x': 0.5, 'y': 0.5}
    dummy_landmarks[scoring_engine.R_KNEE] = {'x': 0.5, 'y': 0.7}

    scores = scoring_engine.get_all_scores(dummy_landmarks, confidence=0.7)
    print("Scores:")
    print(scores)

    assert scores["balance"] < 100.0, "Balance should be penalized for leaning head"
    assert scores["power_proxy"] <= 100.0, "Power proxy should be capped at 100"

    recs = recommendation_engine.generate_recommendations(scores)
    print("\nRecommendations:")
    for r in recs:
        print(f"- [{r['category']} - P{r['priority']}] {r['text']}")

    assert len(recs) > 0, "Should have generated at least one recommendation for bad posture"

if __name__ == "__main__":
    test_scoring_engines()
