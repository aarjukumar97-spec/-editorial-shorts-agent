# Editorial Shorts Agent

Editorial Shorts Agent is the production-shaped foundation for a regional editorial video
workflow. It discovers popular YouTube videos separately for India and the United States,
clusters them into topic opportunities, calculates a transparent score, persists the complete
run, and exposes the evidence through an API.

The product boundary is deliberate:

- Users provide a channel profile, not raw video.
- India uses Hinglish (`hi-Latn`); the United States uses English (`en-US`).
- The intended output is an original researched narrative supported by short, source-tracked
  editorial excerpts.
- No topic is selected, clip acquired, or video published silently.
- Clip duration is not represented as copyright clearance.

## Current vertical slice

Implemented:

- `IN` and `US` regional discovery contracts.
- YouTube `videos.list(chart=mostPopular)` adapter.
- Deterministic fixture provider for local development and CI.
- Topic clustering baseline behind a replaceable intelligence interface.
- Explainable opportunity scoring.
- Durable discovery-run snapshots through SQLAlchemy.
- SQLite locally and PostgreSQL through Docker Compose.
- Explicit workflow states and audit-source labels.
- Editorial clip provenance and risk contracts.
- FastAPI endpoints and automated tests.

Intentionally postponed:

- Multilingual LLM clustering and editorial-angle selection.
- Source-backed research and claim ledger.
- Hinglish script and TTS generation.
- Editorial clip search, acquisition, semantic segment selection, and replacement.
- FFmpeg composition, caption alignment, render QA, and publishing approval.
- Authentication, multi-tenant authorization, billing, and production migrations.

## Architecture

```text
YouTube regional snapshot
  -> provider adapter
  -> topic clusterer
  -> opportunity scorer
  -> persisted DiscoveryRun + audit trail
  -> operator API

Later phases continue from an approved opportunity:
  -> research/claim ledger
  -> Hinglish or English script
  -> voice timing
  -> editorial clip candidates + provenance
  -> render QA
  -> human approval
  -> upload
```

The orchestration rule follows the lesson from `java-healing-observer`: models make bounded
editorial decisions; tools gather evidence and perform media operations; validators and policy
gates decide whether the workflow may advance.

## Run locally

Requirements: Python 3.12+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn editorial_shorts_agent.main:app --reload
```

The default fixture provider requires no credentials. Open `http://localhost:8000/docs`, or run:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/v1/discovery-runs \
  -H 'Content-Type: application/json' \
  -d '{"region":"IN","max_results":25}'
```

The response records `language=hi-Latn`, all source videos, the score components, workflow
states, and the audit trail.

## Use live YouTube data

Create a YouTube Data API key and configure:

```bash
ESA_TREND_PROVIDER=youtube
ESA_YOUTUBE_API_KEY=replace-me
ESA_YOUTUBE_MAX_RESULTS=25
```

Secrets are read from environment variables and are never written into discovery artifacts.

## Run with PostgreSQL

```bash
docker compose up --build
```

The Compose configuration is for local development. Replace its password and storage settings
before using it outside a developer machine.

## Quality checks

```bash
ruff check .
ruff format --check .
pytest -q
```

## Next bounded phase

Add snapshot history and a multilingual model-backed clustering tool. The model output must be
schema validated, retain source-video membership, and fall back to an explicit failure state
rather than inventing a topic. Historical snapshots will replace estimated view velocity with
measured regional deltas.
