# Architecture Document

## Shadow Cricket AI (V1)

This system implements an image-based batting analysis service.

### Components
1. **Flutter App**: Cross-platform frontend for image capture, upload, and rendering results.
2. **FastAPI Backend**: Orchestration layer. Validates uploads, saves raw images, manages PostgreSQL state, and synchronously runs the inference pipeline.
3. **ML Pipeline (Pure Python)**: Uses MediaPipe for landmark extraction, a pre-trained PyTorch (EfficientNet-B0) model for shot classification, and a deterministic heuristic scoring engine for assessing balance, alignment, stance, and a power proxy.

### Constraints & Rules
- **No Video / No Real-Time Analysis**: Explicitly excluded from V1 scope.
- **Power Proxy**: Still images cannot calculate actual physical energy. Power is strictly labeled as a proxy everywhere.
- **Database Migrations**: Managed explicitly by Alembic.
- **Decoupling**: `ml/` scripts contain absolutely no `fastapi` imports. Inference is bundled under a cleanly exposed `run_inference()` function.

### Deviations from Build Plan (if any)
- SQLite was substituted for PostgreSQL in the local development/testing environment due to containerization limitations inside the current sandbox context. In a standard production deployment, PostgreSQL remains the target.
