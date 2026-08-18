from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from typing import Optional

def get_current_user(db: Session = Depends(get_db), x_user_id: Optional[str] = Header(None)) -> User:
    # A mock authentication dependency to retrieve a user
    if not x_user_id:
        # Fallback to test user if no header is provided (for dev convenience)
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
             raise HTTPException(status_code=401, detail="Not authenticated")
        return user

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user ID")

    return user
