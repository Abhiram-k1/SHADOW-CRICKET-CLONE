from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Analysis, Prediction, Score, Recommendation
from app.schemas.analysis import AnalysisResponse, PredictionResponse, ScoreResponse, RecommendationResponse
from app.services.storage_service import storage_service
from app.services.analysis_service import run_full_analysis

router = APIRouter()

MAX_FILE_SIZE = 8 * 1024 * 1024 # 8 MB
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"]

@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_analysis(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"Unsupported file type '{file.content_type}'. Must be one of: {', '.join(ALLOWED_MIME_TYPES)}"
            }
        )

    # Note: Fastapi UploadFile size checking can be tricky asynchronously without reading all into memory,
    # but we can check the file as we read it or via header (if available).
    # Since we use read(), let's check length:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "PAYLOAD_TOO_LARGE",
                "message": f"File size exceeds the limit of {MAX_FILE_SIZE / (1024*1024)} MB"
            }
        )
    # seek back to 0 for storage service to read again
    await file.seek(0)

    # Try decoding image to verify it's not corrupt (using PIL)
    from PIL import Image
    import io
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_IMAGE",
                "message": "The uploaded file is corrupt or not a valid image."
            }
        )

    image_uri = await storage_service.save_upload_file(file)

    analysis = Analysis(
        user_id=current_user.id,
        image_uri=image_uri,
        status="pending"
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Run the orchestrated analysis service synchronously for V1
    run_full_analysis(db, analysis.id, content)

    # Re-fetch the updated analysis and relations
    db.refresh(analysis)
    prediction = db.query(Prediction).filter(Prediction.analysis_id == analysis.id).first()
    score = db.query(Score).filter(Score.analysis_id == analysis.id).first()
    recommendations = db.query(Recommendation).filter(Recommendation.analysis_id == analysis.id).all()

    return AnalysisResponse.model_validate({
        "id": analysis.id,
        "user_id": analysis.user_id,
        "image_uri": analysis.image_uri,
        "status": analysis.status,
        "model_version": analysis.model_version,
        "created_at": analysis.created_at,
        "prediction": prediction,
        "scores": score,
        "recommendations": recommendations
    })

@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if str(analysis.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this analysis")

    # Fetch related records manually or configure lazy="joined" on models
    prediction = db.query(Prediction).filter(Prediction.analysis_id == analysis.id).first()
    score = db.query(Score).filter(Score.analysis_id == analysis.id).first()
    recommendations = db.query(Recommendation).filter(Recommendation.analysis_id == analysis.id).all()

    return AnalysisResponse.model_validate({
        "id": analysis.id,
        "user_id": analysis.user_id,
        "image_uri": analysis.image_uri,
        "status": analysis.status,
        "model_version": analysis.model_version,
        "created_at": analysis.created_at,
        "prediction": prediction,
        "scores": score,
        "recommendations": recommendations
    })
