import sys
import os

# Add ml folder to path so backend can import infer, pose, scoring
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from sqlalchemy.orm import Session
from app.db.models import Analysis, Prediction, Score, Recommendation
from ml.src.infer import run_inference
from ml.src.pose import pose_extractor
from ml.src.scoring import scoring_engine, recommendation_engine

def run_full_analysis(db: Session, analysis_id: str, image_bytes: bytes):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        return

    try:
        # 1. Pose Extraction
        landmarks = pose_extractor.extract_landmarks(image_bytes)
        if not landmarks:
            raise ValueError("No human pose detected in the image.")

        # 2. Inference
        inference_result = run_inference(image_bytes)

        # 3. Scoring
        scores = scoring_engine.get_all_scores(landmarks, confidence=inference_result.confidence)

        # 4. Recommendations
        recs = recommendation_engine.generate_recommendations(scores)

        # 5. Persistence
        # Prediction
        pred_record = Prediction(
            analysis_id=analysis.id,
            shot_class=inference_result.prediction,
            stance_class="front_on", # Mock or add logic if infer engine computes stance
            confidence=inference_result.confidence
        )
        db.add(pred_record)

        # Score
        score_record = Score(
            analysis_id=analysis.id,
            balance=scores["balance"],
            alignment=scores["alignment"],
            stance=scores["stance"],
            power_proxy=scores["power_proxy"]
        )
        db.add(score_record)

        # Recommendations
        for rec in recs:
            rec_record = Recommendation(
                analysis_id=analysis.id,
                priority=rec["priority"],
                text=rec["text"],
                category=rec["category"]
            )
            db.add(rec_record)

        # Update Analysis
        analysis.status = "completed"
        analysis.model_version = inference_result.model_version

        db.commit()

    except Exception as e:
        db.rollback()
        analysis.status = "failed"
        db.commit()
        # Log the raw exception somewhere safe but never return it directly.
        print(f"Analysis {analysis_id} failed: {e}")
