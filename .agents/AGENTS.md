# Development Rules — Multi-Camera Person Tracking System

## Architecture Rules

1. **Event-Driven Only**: AI pipeline → Kafka → Backend → DB. Never bypass Kafka.
2. **Layered Backend**: API Route → Service → Repository. No business logic in routes.
3. **Async Everywhere**: All DB queries, HTTP calls, Kafka ops must use async/await.
4. **Config via Environment**: All secrets and config in `.env`. Never hardcode.

## Code Rules

- **Backend**: Python 3.11+, FastAPI, Pydantic v2 schemas for all I/O, SQLAlchemy 2.0 async.
- **Frontend**: TypeScript strict mode, React 18+, Zustand for client state, TanStack Query for server state.
- **AI Pipeline**: DeepStream configs drive pipeline behavior. Models are NOT committed to git.

## File Placement

- API Gateway routes → `apps/gateway/src/api/v1/`
- AI Pipeline logic → `apps/ai-service/src/`
- Analytics (Clean Arch) → `apps/analytics-service/src/domain|application|infrastructure|presentation/`
- Camera CRUD → `apps/camera-service/src/`
- Search (vector) → `apps/search-service/src/`
- Auth → `apps/auth-service/src/`
- Alerts → `apps/notification-service/src/`
- Cron jobs → `apps/scheduler-service/src/jobs/`
- React features → `apps/web/src/features/<feature-name>/`
- Shared React → `apps/web/src/shared/`
- Shared Python libs → `packages/shared/`
- Data contracts → `packages/contracts/`
- Domain objects → `packages/domain/`
- Test helpers → `packages/testing/`
- DB migrations → `database/postgres/migrations/`
- AI models → `models/` (NOT in git)
- Monitoring configs → `monitoring/`
- K8s manifests → `infrastructure/kubernetes/`

## Reference

Full project structure and rules: `docs/project-structure.md`
