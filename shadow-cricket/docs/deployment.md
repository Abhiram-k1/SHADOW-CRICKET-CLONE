# Deployment Guide (V1)

## Local Development (Docker Compose)
1. Run `cp .env.example .env` and adjust the variables.
2. Run `docker compose up --build`.
   - The FastAPI backend will be available at `http://localhost:8000`.
   - Swagger docs are at `http://localhost:8000/docs`.
   - The database (PostgreSQL container) runs on `5432`.
3. In a separate terminal, run `cd backend && alembic upgrade head` to run migrations.
4. Run `cd backend && python seed.py` to seed a dummy user for the Flutter client.

## Model Training & Artifact Updates
- To train a new model:
  1. `cd ml`
  2. `pip install -r requirements.txt` (or install manually as defined in the plan)
  3. Prepare dataset with `python src/dataset_gen.py`
  4. Preprocess with `python src/preprocess.py`
  5. Train with `python src/train.py`
  6. The `checkpoints/` directory will contain the updated `.pt` file.

## Production Guidelines
- **Reverse Proxy**: Always run Uvicorn behind Nginx or Traefik with TLS/HTTPS.
- **Secrets**: Never commit `.env` containing production JWT secrets or database passwords. Use secret managers (AWS Secrets Manager, GitHub Secrets, etc.).
- **Rate Limiting**: Apply rate limit middleware in FastAPI or at the API Gateway level to prevent abuse.
- **Database**: Do not use `create_all()` in production. Always rely on `alembic` migrations.
- **Model Checkpoints**: Keep ML artifacts out of the git repo. Upload them to object storage or a model registry, and map them via the `MODEL_ARTIFACT_URI` environment variable.
