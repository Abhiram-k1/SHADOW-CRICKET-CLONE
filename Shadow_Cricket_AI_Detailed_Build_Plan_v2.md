# Shadow Cricket AI — Master Build Plan & Jules Task Sheet (v2)

**Prepared for:** Kundurthi Abhiram
**Scope:** V1 (Image-Based Batting Analysis) production-structured prototype, with V2–V4 architecture reserved
**Audience:** Jules (autonomous coding agent) + human reviewer
**Status:** Ready to execute

---

## 1. Purpose of This Revision

This document supersedes the original *Detailed Build Plan* by converting it from a design narrative into an
execution-ready specification: every sprint below is broken into atomic tasks with explicit inputs, outputs,
acceptance criteria, and test requirements, so Jules can work autonomously with minimal clarification loops and
a human reviewer can verify each unit of work in isolation.

**Non-negotiable constraints carried over from the source report and prior build plan:**
- V1 ships image-based analysis only. No video, no real-time gameplay, no multiplayer.
- A single still image cannot measure true bat speed, impact timing, ball trajectory, or physical energy — any
  "power" metric must be labeled as a heuristic/proxy, never as a physical measurement.
- ML code must stay decoupled from the FastAPI layer behind a single inference interface.
- Every prediction is traceable to a `model_version` and a unique `analysis_id`.

---

## 2. Success Criteria for V1 (Exit Definition)

V1 is considered *done*, not merely *functional*, when all of the following hold simultaneously:

| # | Criterion | Verification method |
|---|---|---|
| 1 | Fresh clone + documented setup produces a running stack in under 15 minutes | Timed dry-run by a second engineer or Jules re-run |
| 2 | A batting image uploaded via the API returns a traceable, persisted prediction | Integration test + manual curl |
| 3 | Flutter app completes upload → result round trip against a local backend | Manual + widget test |
| 4 | Evaluation report exists with accuracy, macro-F1, per-class precision/recall, confusion matrix, computed on a held-out split | Committed `ml/reports/eval_v1.md` + artifact |
| 5 | No dataset-specific class is referenced anywhere in code/docs without being present in the training manifest | Automated label-consistency check (Sprint 5) |
| 6 | CI runs backend unit + integration tests and ML smoke tests on every PR | GitHub Actions (or equivalent) green |
| 7 | No secrets committed; `.env.example` matches `config.py` exactly | Secret-scan step in CI |

---

## 3. System Architecture

### 3.1 Logical flow (V1)

```
Flutter (capture/upload)
    │  multipart/form-data
    ▼
FastAPI /api/v1/analyses
    │  validate → persist raw image (object storage) → enqueue/execute inference
    ▼
Inference Service (pure Python, no FastAPI imports)
    │  MediaPipe pose extraction → feature engineering → PyTorch model → deterministic scoring
    ▼
Result assembled (prediction + scores + recommendations + model_version)
    │
    ▼
PostgreSQL (analyses, predictions, scores, recommendations, model_versions)
    │
    ▼
JSON response ──► Flutter Result screen
```

### 3.2 Boundary rule

`backend/app` may **import** `ml/src/infer.py`'s public function (e.g. `run_inference(image_bytes) -> InferenceResult`)
but must never contain training code, dataset paths, or model architecture definitions. This lets the ML team swap
EfficientNet for a ViT checkpoint by publishing a new `model_version` artifact with zero changes to the API layer.

### 3.3 Deployment topology (V1 target)

- FastAPI service: single container, stateless, horizontally scalable.
- PostgreSQL: managed instance (RDS/Cloud SQL/equivalent) or containerized for local/dev.
- Object storage: S3-compatible bucket for raw + processed images; DB stores only URIs.
- Model artifact: stored in object storage or a model registry path, referenced by `MODEL_ARTIFACT_URI`, loaded once
  at process startup (not per-request).

---

## 4. Repository Structure (authoritative)

```
shadow-cricket/
├── README.md
├── LICENSE
├── .env.example
├── docker-compose.yml
├── .github/workflows/ci.yml
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── ml-pipeline.md
│   ├── data-manifest.md
│   └── deployment.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/{health.py,analyses.py,models.py}
│   │   ├── api/deps.py
│   │   ├── core/{config.py,logging.py,security.py}
│   │   ├── db/{session.py,models.py,migrations/}
│   │   ├── schemas/{analysis.py,prediction.py,score.py}
│   │   ├── services/{analysis_service.py,storage_service.py,recommendation_service.py,inference_client.py}
│   │   └── tests/{unit/,integration/}
│   └── requirements.txt
├── ml/
│   ├── data/                # gitignored, manifest only tracked
│   ├── notebooks/
│   ├── src/{dataset.py,preprocess.py,pose.py,features.py,train.py,evaluate.py,infer.py,label_map.py}
│   ├── configs/{baseline.yaml,efficientnet.yaml}
│   ├── checkpoints/         # gitignored
│   ├── reports/             # eval reports committed
│   └── tests/
├── mobile/flutter_app/
│   ├── lib/{screens/,services/,models/,widgets/,state/}
│   └── test/
└── game/unity/README.md     # placeholder only, V3+
```

**Rule for Jules:** never place trained weights, raw datasets, or `.env` files under version control. Add them to
`.gitignore` in Sprint 0.

---

## 5. Data Strategy

| Dataset | Size | Role in V1 | Licensing/action required |
|---|---|---|---|
| Cricket Batsman Stance Dataset (Roboflow) | ~156 images | Pose/stance proof-of-concept | Confirm license terms before redistribution; store attribution in `docs/data-manifest.md` |
| CBSId (Cricket Batting Shots Image Dataset) | 2,160 images, 7 shot classes | Primary V1 classification dataset | Same as above |
| Cricket Shot Dataset (Kaggle) | 10k+ images | Optional diversity/augmentation source | Filter for label noise before mixing in |
| CricShot10 (video) | — | Reserved for V2 | Do not use for V1 training |

**Manifest requirement:** every image used in training must be recorded in `ml/data/manifest.csv` with columns
`image_path, source_dataset, class, split(train/val/test), quality_flag, subject_id(if known)`. This is what
Sprint 5's automated consistency check validates against — no class may appear in `label_map.py` that is absent
from the manifest.

**Split policy:** 70/15/15 train/val/test, stratified by class, with subject-level splitting (no image of the same
batter/session across splits) wherever subject identity is derivable, to prevent leakage.

---

## 6. ML Pipeline (detailed, file-by-file)

| Step | File | Responsibility | Output |
|---|---|---|---|
| 1. Ingest | `dataset.py` | Load manifest, resolve paths, build `torch.utils.data.Dataset` | In-memory dataset objects |
| 2. EDA | `notebooks/01_eda.ipynb` | Class counts, resolution histogram, duplicate/corrupt detection, imbalance ratio | `ml/reports/eda.md` |
| 3. Preprocess | `preprocess.py` | Resize, normalize, dedupe, strip corrupt files — deterministic, seeded | Cleaned image set |
| 4. Pose | `pose.py` | Run MediaPipe, extract 33 landmarks, normalize relative to torso/hip span | `landmarks.parquet` (image_id → 33×(x,y,z,visibility)) |
| 5. Features | `features.py` | Joint angles (elbow, shoulder, hip, knee, ankle), stance width, L/R balance indicators | Feature matrix |
| 6. Labels | `label_map.py` | Single source of truth mapping raw dataset labels → canonical classes; asserts against manifest | `label_map.json` |
| 7. Baseline | `train.py --config configs/baseline.yaml` | Simple classifier (logistic regression / shallow CNN on pose features) to establish a measurable floor | `checkpoints/baseline.pt` + metrics |
| 8. Production model | `train.py --config configs/efficientnet.yaml` | EfficientNet-B0 fine-tune (transfer learning) as first serious baseline; ViT kept as an experiment config, not a blocker | `checkpoints/efficientnet_vX.pt` |
| 9. Evaluate | `evaluate.py` | Accuracy, macro-F1, per-class precision/recall, confusion matrix on held-out test split | `ml/reports/eval_v1.md` |
| 10. Package | `infer.py` | Load artifact + preprocessing + label map behind one function: `run_inference(image_bytes) -> InferenceResult` | Versioned inference module |

### 6.1 Baseline model targets (minimum bar before production model work starts)

- Baseline (pose-feature classifier): document actual accuracy/macro-F1 — no hard-coded target, since dataset
  quality is unproven; the number itself becomes the floor the EfficientNet model must beat.
- EfficientNet-B0 fine-tune: must exceed the baseline on macro-F1 on the held-out test split, or the sprint is not
  considered complete — investigate class imbalance, augmentation, or label noise before proceeding.

### 6.2 Training configuration (starting point, tune during Sprint 5)

- Backbone: `efficientnet_b0`, ImageNet-pretrained, fine-tune last block + new classification head first; unfreeze
  progressively if underfitting.
- Optimizer: AdamW, initial LR `3e-4` for the head, `3e-5` for unfrozen backbone layers.
- Batch size: 32 (adjust to available memory).
- Augmentation: horizontal considerations must respect cricket handedness (do not naively flip — left-/right-handed
  stance is semantically meaningful); prefer color jitter, slight rotation, crop, and brightness/contrast changes.
- Early stopping on validation macro-F1, patience 5 epochs.
- Class imbalance: weighted loss or oversampling if class counts diverge by more than ~3x.

---

## 7. Pose & Deterministic Scoring Design

**Guardrail (repeat from source report):** a still image cannot measure bat velocity, impact timing, ball
trajectory, or true physical power. `power_score` must always be documented and returned as a heuristic/proxy.

| Metric | Conceptual formula | Notes |
|---|---|---|
| `balance_score` | 100 − weighted penalty for lateral/forward-backward center-of-mass asymmetry vs. supported stance reference | Deterministic, no model call |
| `alignment_score` | 100 − weighted deviation of shoulder/hip/knee/foot alignment angles from stance-appropriate reference ranges | Deterministic |
| `stance_score` | Weighted combination of stance width ratio, knee flexion angle, torso lean | Deterministic |
| `power_proxy` | Weighted blend of model confidence + posture proxies (hip-shoulder separation angle, front-knee flexion) | Explicitly labeled "proxy, not a physical measurement" in every API response and UI surface |

**Recommendation engine (V1):**
1. Threshold each deterministic score; anything below its threshold becomes a candidate observation.
2. Rank candidates by (a) how far below threshold, (b) coaching priority weight (e.g., balance > alignment > stance).
3. Return the top 2–3 only — never a long list.
4. Use fixed, tested templates in V1 (e.g., "Keep the head more stable over the front knee.") so output is
   deterministic and unit-testable. A learned coaching model is explicitly post-V1 (see backlog).

---

## 8. FastAPI Contract

### 8.1 Endpoints

| Method | Path | Purpose | Auth (V1) |
|---|---|---|---|
| GET | `/health` | Liveness/readiness | None |
| POST | `/api/v1/analyses` | Upload image, create analysis | Required |
| GET | `/api/v1/analyses/{id}` | Retrieve one analysis | Required, owner-only |
| GET | `/api/v1/analyses` | List current user's analyses (paginated) | Required |
| GET | `/api/v1/models` | List deployed model versions | Required (admin scope optional) |
| GET | `/api/v1/analyses/{id}/image` | Signed/authorized image access | Required, owner-only |

### 8.2 Request/response schemas (Pydantic-level detail)

**POST `/api/v1/analyses`** — `multipart/form-data`, field `image` (jpeg/png, ≤ 8 MB, min 224×224 px).

Synchronous response (V1 assumption — inference must complete in an acceptable request window; move to async/queue
if p95 latency exceeds ~3s):

```json
{
  "analysis_id": "a1b2c3d4",
  "status": "completed",
  "created_at": "2026-06-20T10:15:00Z",
  "prediction": {
    "stance_class": "front_on",
    "shot_class": "cover_drive",
    "confidence": 0.87
  },
  "scores": {
    "balance": 78,
    "alignment": 84,
    "stance": 81,
    "power_proxy": 72
  },
  "recommendations": [
    "Keep the head more stable over the front knee.",
    "Maintain a consistent base width through the shot."
  ],
  "model_version": "shadow-v1.0.0"
}
```

**Error contract (all endpoints):**

```json
{
  "error": {
    "code": "invalid_image",
    "message": "Uploaded file is not a decodable image.",
    "analysis_id": null
  }
}
```

| HTTP status | Example `code` | Trigger |
|---|---|---|
| 400 | `invalid_image` | Corrupt file, wrong MIME, decode failure |
| 400 | `image_too_large` | Exceeds size limit |
| 401 | `unauthenticated` | Missing/invalid credentials |
| 403 | `forbidden` | Accessing another user's analysis |
| 404 | `analysis_not_found` | Unknown `analysis_id` |
| 500 | `inference_failure` | Unexpected model/pipeline error (never leaks stack trace or file paths) |

### 8.3 API rules

- `/api/v1` versioning from day one; breaking changes require `/api/v2`.
- Validate MIME type, size, and successful decode before any inference call.
- Every response includes `analysis_id` and `model_version` where applicable.
- Never expose filesystem paths, internal model class names, or stack traces in responses.
- Rate limit before public launch (see Security section).

---

## 9. PostgreSQL Data Model

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE model_versions (
    version TEXT PRIMARY KEY,
    artifact_uri TEXT NOT NULL,
    metrics_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_model_versions_active ON model_versions(active);

CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    image_uri TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','completed','failed')),
    model_version TEXT REFERENCES model_versions(version),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_created_at ON analyses(created_at);

CREATE TABLE predictions (
    analysis_id UUID PRIMARY KEY REFERENCES analyses(id) ON DELETE CASCADE,
    stance_class TEXT,
    shot_class TEXT,
    confidence REAL
);

CREATE TABLE scores (
    analysis_id UUID PRIMARY KEY REFERENCES analyses(id) ON DELETE CASCADE,
    balance REAL,
    alignment REAL,
    stance REAL,
    power_proxy REAL
);

CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    priority INT NOT NULL,
    text TEXT NOT NULL,
    category TEXT
);
CREATE INDEX idx_recommendations_analysis_id ON recommendations(analysis_id);
```

**Persistence rules:** Alembic (or equivalent) migrations only — no `create_all()` in production. Store image
binaries in object storage, only URIs in Postgres. Do not collect unnecessary personal data in V1 (email only).

---

## 10. Flutter App

| Screen | Function | V1 |
|---|---|---|
| Home | Start new analysis / recent analyses | Yes |
| Capture/Upload | Camera or gallery image | Yes |
| Processing | Upload + progress indicator | Yes |
| Result | Prediction, scores, recommendations | Yes |
| History | Previous analyses list | Recommended |
| Profile | Minimal user settings | Minimal |
| Live Coach | Real-time video feedback | V2+ |
| Game | Gameplay interface | V3+ |

**State management:** pick one pattern (Riverpod or Bloc) in Sprint 0 and use it consistently — do not mix
patterns across screens.

**Result screen layout priority:** primary prediction at top → 3–4 score cards → top recommendations →
collapsible "How was this calculated?" section → model version/timestamp in a secondary details row.

---

## 11. Sprint-by-Sprint Task Sheet for Jules

Each sprint must be fully implemented, tested, and committed before the next begins. Commit format:
`feat(scope): description`, `test(scope): description`, `docs: description`.

### Sprint 0 — Repository & environment scaffold
- [ ] Create monorepo structure exactly as in Section 4.
- [ ] `.gitignore` excludes `ml/checkpoints/`, `ml/data/*` (except `manifest.csv`), `.env`, build artifacts.
- [ ] `docker-compose.yml` brings up backend + Postgres with one command.
- [ ] `.env.example` lists every variable from Section 13, placeholders only.
- [ ] CI workflow file exists (even if only running lint + placeholder tests).
- **DoD:** `docker compose up` succeeds; `/health` (stub) returns 200; CI pipeline runs green on an empty test suite.

### Sprint 1 — Database & migrations
- [ ] Implement schema from Section 9 via migrations (not raw SQL execution at boot).
- [ ] Migration up/down verified locally.
- [ ] Seed script for a test user.
- **DoD:** `alembic upgrade head` (or equivalent) creates all tables; downgrade cleanly reverses.

### Sprint 2 — Image upload API (no inference yet)
- [ ] `POST /api/v1/analyses` accepts image, validates MIME/size/decodability, stores in object storage, persists
      an `analyses` row with `status=pending`.
- [ ] Reject invalid files with the error contract from Section 8.3.
- [ ] `GET /api/v1/analyses/{id}` returns the row (prediction/scores null while pending).
- **DoD:** Integration tests cover valid upload, oversized file, wrong MIME, corrupt file, unauthenticated request.

### Sprint 3 — MediaPipe pose pipeline
- [ ] `pose.py` extracts and normalizes 33 landmarks for a given image.
- [ ] Smoke test on a fixture image produces non-null landmarks with expected shape.
- [ ] Landmarks persisted separately from raw images (parquet/JSON in object storage or a dedicated table).
- **DoD:** Pose extraction runs deterministically on the fixture image in CI.

### Sprint 4 — Dataset manifest, EDA, cleaning
- [ ] Download/organize the four datasets per Section 5; produce `manifest.csv`.
- [ ] Run EDA notebook; commit `ml/reports/eda.md` with class counts, imbalance ratio, duplicate/corrupt findings.
- [ ] `preprocess.py` cleans and standardizes images without destroying posture-relevant detail.
- **DoD:** Manifest exists, is stratified-splittable, and every class in it is documented in `docs/data-manifest.md`.

### Sprint 5 — ML baseline + production model
- [ ] `label_map.py` asserts every label maps to a class present in the manifest — build fails otherwise.
- [ ] Train baseline (pose-feature classifier); record metrics.
- [ ] Train EfficientNet-B0 fine-tune per Section 6.2; must beat baseline macro-F1 on held-out test split.
- [ ] `evaluate.py` produces `ml/reports/eval_v1.md` with accuracy, macro-F1, per-class precision/recall, confusion
      matrix.
- [ ] Check for subject-level leakage between splits where subject identity is derivable.
- **DoD:** Evaluation report committed; EfficientNet model outperforms baseline; no invented/undocumented classes.

### Sprint 6 — Model packaging & inference interface
- [ ] `infer.py` exposes `run_inference(image_bytes) -> InferenceResult` loading artifact, preprocessing, and label
      map once at import/startup.
- [ ] Artifact versioned and registered in `model_versions` table (via a small admin script or migration seed).
- [ ] No FastAPI imports anywhere under `ml/`.
- **DoD:** Calling `run_inference` from a plain Python script (no server running) returns a valid result.

### Sprint 7 — Deterministic scoring & recommendation engine
- [ ] Implement `balance_score`, `alignment_score`, `stance_score`, `power_proxy` per Section 7 formulas.
- [ ] Implement recommendation engine: threshold → rank → top 2–3 → fixed templates.
- [ ] Unit tests for each scoring function against known landmark fixtures (edge cases: perfectly balanced,
      maximally asymmetric).
- **DoD:** Deterministic scoring is reproducible (same input → same output) and independently unit-tested from the
  model.

### Sprint 8 — Full analysis service integration
- [ ] Wire upload → pose → inference → scoring → recommendations → persistence into one orchestrated service call.
- [ ] `POST /api/v1/analyses` returns the full response contract from Section 8.2 synchronously.
- [ ] `status` transitions `pending → completed` or `pending → failed` (with error persisted, not raw exception).
- **DoD:** End-to-end fixture test: real image in → full JSON contract out, matching Section 8.2 shape.

### Sprint 9 — Flutter client
- [ ] Implement screens per Section 10 (Home, Capture/Upload, Processing, Result at minimum).
- [ ] Networking layer calls the real API (configurable base URL) and handles the error contract gracefully.
- [ ] Result screen renders prediction, scores, recommendations per the layout priority in Section 10.
- **DoD:** Manual run: pick/capture an image, see a real result from a locally running backend; at least one widget
  test per screen.

### Sprint 10 — Integration tests, security hardening, deployment docs
- [ ] Full-stack integration test: API + inference + DB together (no mocks) using a fixture image.
- [ ] Apply security rules from Section 13.
- [ ] `docs/deployment.md` walks a fresh developer through local and (at minimum) containerized deployment.
- [ ] `docs/architecture.md` finalized to match what was actually built (update if implementation diverged from
      this plan — divergences must be explained here, not silently left undocumented).
- **DoD:** All Section 2 success criteria pass.

---

## 12. Testing & Quality Gates

**Backend:**
- Health endpoint test.
- Image validation tests: valid, oversized, unsupported type, corrupted.
- Analysis lifecycle persistence test (pending → completed/failed).
- Inference service mocked out for fast unit tests; real inference exercised only in the Sprint 10 integration test.
- Authorization tests: cannot read another user's analysis.

**ML:**
- Dataset loader test.
- Label mapping consistency test (manifest ↔ `label_map.py`).
- Preprocessing determinism test (same input → same output bytes/tensor).
- Pose extraction smoke test.
- Model load/inference smoke test.
- Evaluation script produces a well-formed report with all required metrics.
- Subject-leakage check where subject IDs are available.

**Acceptance gates (all must pass before V1 is declared complete):**

| Gate | Pass condition |
|---|---|
| Reproducibility | Fresh setup runs the complete V1 pipeline per `docs/deployment.md` |
| API correctness | OpenAPI schema (auto-generated by FastAPI) matches implemented endpoints |
| ML correctness | Evaluation generated from a genuinely held-out test split, not train data |
| Traceability | Every persisted prediction records a `model_version` |
| Failure handling | Bad inputs return the documented error contract, never a raw stack trace |
| Mobile integration | Flutter completes upload → result flow against a running backend |
| Documentation | README covers setup, train, test, infer, and run commands exactly as used in CI |

---

## 13. Security, Configuration & Deployment

**Environment variables (`.env.example`):**

```
DATABASE_URL=
STORAGE_BUCKET=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
MODEL_ARTIFACT_URI=
MODEL_VERSION=
API_ENV=development
LOG_LEVEL=INFO
JWT_SECRET=
RATE_LIMIT_PER_MINUTE=60
```

**Rules:**
- Never commit secrets, API keys, or credentials of any kind.
- `.env.example` must always contain placeholders only, kept in sync with `core/config.py`.
- Restrict upload size (≤ 8 MB default) and content type (jpeg/png only).
- Require authentication before exposing private analysis history or images.
- Use HTTPS in any deployed (non-local) environment.
- Log `analysis_id`, request duration, `model_version`, and failure reason/category — never raw image bytes or
  full stack traces in production logs.
- Add rate limiting (`RATE_LIMIT_PER_MINUTE`) before any public launch.
- CI must include a secret-scanning step (e.g., gitleaks or equivalent).

**Deployment target:** FastAPI service and PostgreSQL may run separately or via a managed container platform;
cloud provider is intentionally unspecified, matching the source report's scope. Keep the model artifact external
to the code repository once it grows beyond a trivial size.

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dataset too small/imbalanced for reliable classification | High | High | Baseline-first approach surfaces this early (Sprint 5); consider augmentation or narrowing class set |
| Pose extraction fails on low-quality/occluded images | Medium | Medium | Explicit `quality_flag` in manifest; graceful degradation (partial scores) rather than hard failure |
| Users misinterpret `power_proxy` as a physical measurement | Medium | Medium | Mandatory disclaimer text in API docs and Flutter UI, not just this document |
| Scope creep toward V2/V3 features mid-sprint | Medium | High | Sprint task sheet is the contract; new ideas go to the Section 15 backlog, not into V1 sprints |
| Synchronous inference latency degrades UX at scale | Low (V1 traffic) | Medium | Documented escalation path to async/queue-based inference if p95 latency exceeds ~3s |

---

## 15. Product Backlog (Post-V1)

| Priority | Item | Phase |
|---|---|---|
| P0 | Reliable image analysis vertical slice | V1 |
| P0 | Model/version traceability | V1 |
| P0 | Flutter result UI | V1 |
| P1 | Analysis history screen | V1 |
| P1 | Model evaluation dashboard | V1 |
| P1 | Video upload + frame sampling | V2 |
| P1 | Temporal pose model (CricShot10) | V2 |
| P2 | Real-time inference optimization | V3 |
| P2 | Unity game-event bridge | V3 |
| P3 | Personalized AI coach (learned recommendation model) | V4 |
| P3 | Multiplayer + esports/leaderboard layer | V4 |

---

## 16. Traceability to Source Materials

- Vision, roadmap (V1–V4), candidate datasets, ML pipeline stages, and recommended stack are carried forward
  unchanged from the original *Product Research & Development Report* (15 June 2026) and the prior *Detailed Build
  Plan*.
- This revision adds: sprint-level task decomposition with explicit Definitions of Done, full SQL DDL, a complete
  error contract, training hyperparameter starting points, a risk register, and measurable exit criteria — none of
  which were specified in the original two-document set, and all of which should be treated as proposed engineering
  detail rather than facts stated in the source report.

---

## 17. Ready-to-Paste Jules Master Instruction

```
You are implementing Shadow Cricket AI, V1 only (image-based batting analysis).

HARD RULES
1. Do not build video analysis, real-time gameplay, or multiplayer in V1.
2. Never claim a still image measures true bat speed, impact timing, trajectory, or physical power —
   label any such metric "proxy"/"estimate" everywhere it appears (API docs, code comments, UI copy).
3. Keep ml/ free of any FastAPI import. Expose exactly one inference entrypoint:
   run_inference(image_bytes) -> InferenceResult.
4. Every model artifact gets a model_version; every analysis persists it.
5. Use database migrations only — never create_all() against a production database.
6. Never invent or hard-code a class label that is absent from ml/data/manifest.csv.
7. Never commit secrets; .env.example must stay in sync with core/config.py.
8. Follow the exact repository structure in Section 4 of this document.

EXECUTION ORDER
Work through Section 11, Sprint 0 → Sprint 10, in order. Do not start a sprint until the previous
sprint's Definition of Done is met and committed. If you must deviate from this plan, update
docs/architecture.md in the same commit explaining why.

DONE MEANS
Every checkbox in Section 11 is complete, every gate in Section 12 passes, and Section 2's five
success criteria all hold on a fresh clone.
```

**END OF BUILD PLAN v2**
