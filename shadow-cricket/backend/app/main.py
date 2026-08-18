from fastapi import FastAPI
from app.api.routes import health, analyses
from app.core.security import SecurityMiddleware

app = FastAPI(title="Shadow Cricket AI")

app.add_middleware(SecurityMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1/analyses", tags=["analyses"])
