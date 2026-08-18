import os
import sys

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '.')))

from app.db.session import SessionLocal
from app.db.models import User, ModelVersion

def seed():
    db = SessionLocal()
    try:
        # Check if user already exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(email="test@example.com")
            db.add(test_user)
            db.commit()
            print(f"Created test user with ID: {test_user.id}")
        else:
            print("Test user already exists.")

        # Seed model version
        test_model = db.query(ModelVersion).filter(ModelVersion.version == "v1.0.0").first()
        if not test_model:
            test_model = ModelVersion(
                version="v1.0.0",
                artifact_uri="checkpoints/efficientnet_v1.pt",
                metrics_json={"accuracy": 0.0},
                active=True
            )
            db.add(test_model)
            db.commit()
            print("Created test model version v1.0.0")
        else:
            print("Model version v1.0.0 already exists.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
