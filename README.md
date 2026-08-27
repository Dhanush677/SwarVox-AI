# SwarVox AI

Event-driven AI voice agent platform for inbound and outbound business calls.

SwarVox is built around a core product principle:

> Business events trigger autonomous customer communication workflows.

Phase 1 implements the foundation:

- FastAPI backend
- PostgreSQL-ready SQLAlchemy models
- Idempotent event ingestion API
- Workflow matching
- Outbound call orchestration through a provider abstraction
- Mock telephony provider for local demos
- Minimal React dashboard and lead form

See [docs/architecture.md](docs/architecture.md) for the architecture and development phases.
