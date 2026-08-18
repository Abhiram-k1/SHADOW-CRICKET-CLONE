from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Float, Integer
from sqlalchemy.sql import func
import uuid
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    version = Column(String, primary_key=True)
    artifact_uri = Column(String, nullable=False)
    metrics_json = Column(JSON, nullable=False)
    active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    image_uri = Column(String, nullable=False)
    status = Column(String, nullable=False) # 'pending', 'completed', 'failed'
    model_version = Column(String, ForeignKey("model_versions.version"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

class Prediction(Base):
    __tablename__ = "predictions"
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True)
    stance_class = Column(String)
    shot_class = Column(String)
    confidence = Column(Float)

class Score(Base):
    __tablename__ = "scores"
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(Float)
    alignment = Column(Float)
    stance = Column(Float)
    power_proxy = Column(Float)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    category = Column(String)
