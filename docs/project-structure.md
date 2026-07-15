# 📐 Project Structure & Development Rules

> **Tài liệu này là "source of truth" cho cấu trúc dự án.**
> Mọi developer (và AI agent) PHẢI tuân theo các quy tắc trong đây khi viết code.

---

## Tổng quan kiến trúc

Hệ thống theo mô hình **Event-Driven Microservices** với **Clean Architecture**, triển khai dạng **monorepo**:

```
┌───────────────────────────────────────────────────────────────────┐
│                        apps/web (React)                          │
│              Dashboard · Live Monitor · Search · Alerts           │
└────────────────────────────┬──────────────────────────────────────┘
                             │ HTTP / WebSocket
┌────────────────────────────▼──────────────────────────────────────┐
│                      apps/gateway (FastAPI)                       │
│              API Gateway · Auth · Rate Limit · WebSocket          │
└──┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
   │          │          │          │          │ gRPC / HTTP
┌──▼───┐  ┌──▼───┐  ┌──▼────┐  ┌──▼───┐  ┌──▼──────┐
│camera│  │search│  │analyt.│  │alert │  │  auth   │
│ svc  │  │ svc  │  │  svc  │  │ svc  │  │  svc   │
└──────┘  └──┬───┘  └──┬────┘  └──────┘  └────────┘
             │         │
             │    ┌────▼─────┐
             │    │  Kafka   │
             │    └────┬─────┘
             │         │
         ┌───▼─────────▼──────────────────────────┐
         │          apps/ai-service                │
         │  DeepStream · YOLO · ReID · MTMC        │
         └─────────────────────────────────────────┘
```

---

## Cấu trúc thư mục (Enterprise Monorepo)

### `apps/` — Các ứng dụng deploy độc lập

Mỗi service là một **deployable unit** riêng biệt, có Dockerfile, tests, config riêng.

---

#### `apps/web/` — React Frontend Dashboard

> **Ngôn ngữ:** TypeScript · **Framework:** React 18 + Vite + Zustand + TanStack Query

```
apps/web/
├── src/
│   ├── app/                    # Bootstrap: App.tsx, router.tsx, providers.tsx
│   │                           #   → App shell, route definitions, context providers
│   │
│   ├── features/               # ── FEATURE-BASED MODULES ──
│   │   ├── dashboard/          # Dashboard: stats, charts, recent activity
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── components/     #   StatsCard, ActivityChart
│   │   │   └── hooks/          #   useDashboard
│   │   ├── live-monitor/       # Multi-camera real-time view
│   │   │   ├── LiveMonitorPage.tsx
│   │   │   └── components/     #   CameraGrid, CameraPlayer, TrackingOverlay
│   │   ├── person-search/      # Search by image/text
│   │   │   ├── PersonSearchPage.tsx
│   │   │   └── components/     #   ImageUpload, SearchResults
│   │   ├── tracking-history/   # Replay person trail on map
│   │   │   ├── TrackingHistoryPage.tsx
│   │   │   └── components/     #   TrailMap, Timeline
│   │   ├── camera-management/  # Camera CRUD + status
│   │   │   ├── CameraManagementPage.tsx
│   │   │   └── components/     #   CameraForm, CameraTable
│   │   ├── alert-center/       # Alert management
│   │   └── settings/           # System settings
│   │
│   ├── shared/                 # ── SHARED ACROSS FEATURES ──
│   │   ├── components/
│   │   │   ├── layout/         #   Sidebar, Header, MainLayout
│   │   │   └── common/         #   Button, Modal, Table, Badge, Spinner
│   │   ├── hooks/              #   useWebSocket, useAuth
│   │   ├── stores/             #   Zustand: camera, tracking, alert, auth stores
│   │   ├── types/              #   TypeScript type definitions
│   │   └── utils/              #   api-client, formatters, validators
│   │
│   ├── assets/                 # Images, icons, static files
│   └── styles/                 # globals.css, variables.css, design tokens
```

**RULES:**
1. **Feature-first** — Mỗi feature là 1 folder tự chứa: page + components + hooks. Import cross-feature qua `shared/`.
2. **Không gọi API trực tiếp** — Dùng hooks (TanStack Query) trong `shared/hooks/` hoặc feature hooks.
3. **State**: Client state → `shared/stores/` (Zustand). Server state → TanStack Query. KHÔNG mix.
4. **Types trước, code sau** — Define types trong `shared/types/` trước khi code component.

---

#### `apps/gateway/` — API Gateway

> **Ngôn ngữ:** Python 3.11+ · **Framework:** FastAPI
>
> **Vai trò:** Single entry point cho frontend. Route requests đến đúng service, handle auth, rate limiting, WebSocket.

```
apps/gateway/
├── src/
│   ├── main.py                 # FastAPI entry point
│   ├── api/v1/
│   │   └── routes.py           # Proxy routes → downstream services
│   ├── middleware/
│   │   ├── rate_limiter.py     # Rate limiting per user/IP
│   │   ├── cors.py             # CORS configuration
│   │   └── logging.py          # Request/response structured logging
│   ├── websocket/
│   │   ├── manager.py          # WebSocket connection manager
│   │   └── handlers.py         # Real-time event handlers
│   ├── auth/
│   │   ├── jwt.py              # JWT validation + decode
│   │   └── permissions.py      # RBAC permission checks
│   └── config/
│       └── settings.py         # Pydantic Settings
```

**RULES:**
1. **Gateway KHÔNG chứa business logic** — Chỉ route, auth, rate limit. Logic ở downstream services.
2. **Mọi request phải qua gateway** — Frontend KHÔNG gọi trực tiếp service khác.
3. **WebSocket hub** — Gateway là nơi duy nhất manage WebSocket connections.

---

#### `apps/ai-service/` — DeepStream AI Pipeline

> **Ngôn ngữ:** Python + C++ · **Runtime:** NVIDIA DeepStream 7.x + TensorRT + CUDA
>
> **Vai trò:** Xử lý video real-time, detect/track/ReID, gửi events qua Kafka.

```
apps/ai-service/
├── src/
│   ├── main.py                 # Pipeline entry point
│   ├── pipelines/              # ── PIPELINE CONSTRUCTION ──
│   │   ├── deepstream_pipeline.py   # GStreamer pipeline builder
│   │   ├── pipeline_builder.py      # Fluent API to build pipelines
│   │   └── pipeline_config.py       # Pipeline config parser
│   │
│   ├── inference/              # ── MODEL INFERENCE ──
│   │   ├── detector.py         # YOLOv8 detector wrapper
│   │   ├── triton_client.py    # Triton Inference Server client
│   │   └── batch_processor.py  # Batch processing for GPU efficiency
│   │
│   ├── tracker/                # ── SINGLE-CAMERA TRACKING ──
│   │   ├── nvdcf_tracker.py    # NVIDIA DCF tracker wrapper
│   │   ├── bytetrack.py        # ByteTrack alternative
│   │   └── tracker_config.py   # Tracker parameter management
│   │
│   ├── reid/                   # ── CROSS-CAMERA RE-IDENTIFICATION ──
│   │   ├── feature_extractor.py     # Extract person embeddings
│   │   ├── gallery_manager.py       # Identity gallery (known persons)
│   │   ├── mtmc_association.py      # Multi-Target Multi-Camera matching
│   │   └── spatial_constraints.py   # Camera topology + transition rules
│   │
│   ├── stream/                 # ── VIDEO STREAM MANAGEMENT ──
│   │   ├── rtsp_source.py      # RTSP stream connection + reconnect
│   │   ├── stream_manager.py   # Multi-stream lifecycle management
│   │   └── decoder.py          # Hardware-accelerated video decode
│   │
│   ├── plugins/                # ── CUSTOM DEEPSTREAM PLUGINS ──
│   │   ├── custom_parser.py    # Custom bounding box parser
│   │   └── probe_callbacks.py  # GStreamer probe functions
│   │
│   ├── events/                 # ── EVENT PUBLISHING ──
│   │   ├── kafka_producer.py   # Publish tracking events → Kafka
│   │   └── event_schemas.py    # Event structure definitions
│   │
│   ├── storage/                # ── CROP/CLIP STORAGE ──
│   │   ├── crop_saver.py       # Save person crops to MinIO
│   │   └── minio_client.py     # MinIO S3 client
│   │
│   └── utils/                  # ── UTILITIES ──
│       ├── bbox.py, nms.py, embedding.py, gpu_monitor.py
│
├── configs/                    # Pipeline configs (KHÔNG hardcode trong code)
│   ├── deepstream_app.yml      # Main pipeline config
│   ├── tracker_config.yml      # Tracker parameters
│   ├── pgie_yolov8.txt         # Primary detector config
│   ├── sgie_reid.txt           # Secondary ReID config
│   └── triton_config.pbtxt     # Triton model serving config
```

**RULES:**
1. **Output chỉ qua Kafka** — KHÔNG gọi database hay API trực tiếp. Publish events → `tracking-events` topic.
2. **Config-driven** — Thay đổi model/tracker bằng config file, KHÔNG sửa code.
3. **Models KHÔNG commit git** — File `.engine`, `.onnx`, `.trt` trong `.gitignore`. Dùng `models/scripts/` để generate.
4. **GPU constraint (dev)** — GTX 1650 4GB: YOLOv8n + OSNet-x0.25, max 2-4 cameras @ 720p.

---

#### `apps/analytics-service/` — Business Logic (Clean Architecture)

> **Vai trò:** Consume tracking events từ Kafka, xử lý business logic, lưu DB, tạo analytics.
>
> **Pattern:** Clean Architecture (Domain-Driven Design)

```
apps/analytics-service/
├── src/
│   ├── domain/                 # ── DOMAIN LAYER (Innermost) ──
│   │   │                       #   Pure business rules, NO framework dependency
│   │   ├── entities/           #   TrackingEvent, PersonIdentity, Zone
│   │   ├── value_objects/      #   BoundingBox, EmbeddingVector, CameraPosition
│   │   ├── repositories/      #   Abstract interfaces (ports)
│   │   └── services/           #   TrackingDomainService, HeatmapService
│   │
│   ├── application/            # ── APPLICATION LAYER ──
│   │   │                       #   Use cases, orchestration, DTOs
│   │   ├── use_cases/          #   ProcessTrackingEvent, GenerateAnalytics, GetPersonTrail
│   │   └── dto/                #   TrackingDTO, AnalyticsDTO
│   │
│   ├── infrastructure/         # ── INFRASTRUCTURE LAYER ──
│   │   │                       #   Concrete implementations (adapters)
│   │   ├── persistence/        #   SQLAlchemy repos (implement domain interfaces)
│   │   ├── messaging/          #   Kafka consumer/producer
│   │   └── external/           #   Qdrant client, MinIO storage
│   │
│   └── presentation/           # ── PRESENTATION LAYER (Outermost) ──
│       ├── api/v1/             #   FastAPI routes (tracking, analytics)
│       └── consumers/          #   Kafka consumer entry points
```

**RULES:**
1. **Dependency inversion** — Domain layer KHÔNG import từ infrastructure. Infrastructure implement domain interfaces.
2. **Use cases là entry point** — Mọi business operation phải qua use case. Route/consumer chỉ gọi use case.
3. **DTOs at boundaries** — Domain entities KHÔNG leak ra API. Convert → DTO ở application layer.

---

#### Các services còn lại (cấu trúc tương tự)

| Service | Vai trò | Key files |
|:--------|:--------|:----------|
| `apps/auth-service/` | JWT auth, user management, RBAC | `auth_routes.py`, `user.py`, `role.py`, `token_service.py` |
| `apps/camera-service/` | Camera CRUD, RTSP health check, grouping | `camera_routes.py`, `stream_routes.py`, `health_checker.py` |
| `apps/notification-service/` | Alerts qua WebSocket, email, webhook | `alert_routes.py`, `websocket.py`, `email.py`, `webhook.py` |
| `apps/scheduler-service/` | Cron jobs: cleanup, health check, reports | `cleanup_old_data.py`, `health_check_cameras.py`, `generate_reports.py` |
| `apps/search-service/` | Person search by image/text (vector DB) | `search_routes.py`, `qdrant_store.py`, `embedding_indexer.py` |

**RULE chung cho mọi service:**
- Mỗi service có `Dockerfile`, `pyproject.toml`, `tests/`, `src/config/settings.py` riêng.
- Config đọc từ environment (.env). KHÔNG hardcode.
- Expose health endpoint: `GET /health`.
- Export Prometheus metrics: `GET /metrics`.

---

### `packages/` — Shared Libraries

> Code dùng chung giữa nhiều services. Import dạng package, KHÔNG copy-paste.

```
packages/
├── shared/                     # ── UTILITIES DÙNG CHUNG ──
│   ├── constants/              #   kafka_topics.py, error_codes.py
│   ├── config/                 #   base_settings.py (Pydantic base)
│   ├── exceptions/             #   base.py (BaseAppException), service.py
│   ├── logger/                 #   structured.py (structlog config)
│   ├── middleware/             #   request_id.py, timing.py
│   ├── decorators/             #   retry.py, cache.py
│   ├── helpers/                #   datetime.py, pagination.py
│   └── utils/                  #   validators.py
│
├── contracts/                  # ── DATA CONTRACTS (Single Source of Truth) ──
│   ├── dto/                    #   Pydantic DTOs: camera, person, tracking, alert, search
│   ├── events/                 #   Kafka event schemas: tracking_event, alert_event, camera_event
│   ├── schemas/                #   Avro schemas (.avsc)
│   ├── protobuf/               #   gRPC proto files: embedding.proto, tracking.proto
│   └── openapi/                #   OpenAPI specs: gateway.yaml
│
├── sdk/                        # ── SERVICE SDK ──
│   ├── python/                 #   Python SDK: api_client, camera_sdk, search_sdk
│   └── typescript/             #   TypeScript SDK (for frontend)
│
├── domain/                     # ── SHARED DOMAIN OBJECTS ──
│   ├── entities/               #   Camera, Person, TrackingEvent, Alert
│   ├── value_objects/          #   BoundingBox, Embedding, GeoLocation
│   └── enums/                  #   CameraStatus, AlertSeverity, TrackingStatus
│
├── testing/                    # ── TEST INFRASTRUCTURE ──
│   ├── fixtures/               #   db.py (test DB), kafka.py (test Kafka)
│   ├── factories/              #   camera_factory.py, person_factory.py
│   └── mocks/                  #   mock_qdrant.py, mock_kafka.py
│
└── ui/                         # ── SHARED REACT COMPONENTS ──
    ├── components/             #   Reusable UI components (design system)
    ├── hooks/                  #   Shared React hooks
    └── styles/                 #   Shared CSS/design tokens
```

**RULES:**
1. **contracts/ là single source of truth** — Mọi data format giữa services PHẢI define ở đây.
2. **Backward compatible** — Thay đổi schema phải backward compatible (thêm optional field, KHÔNG xóa/rename).
3. **Version packages** — Mỗi package có `pyproject.toml` riêng, version theo semver.

---

### `database/` — Database Schemas & Migrations

```
database/
├── postgres/
│   ├── schema.sql              # Full schema (reference)
│   ├── migrations/             # Alembic migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/           # Auto-generated migration files
│   └── seed/                   # Test/dev seed data
│       ├── seed_cameras.sql
│       └── seed_users.sql
├── redis/
│   └── redis.conf              # Redis configuration
├── kafka/
│   └── topics/topics.yml       # Kafka topic definitions
└── minio/
    └── buckets/init-buckets.sh # Auto-create S3 buckets
```

**RULES:**
1. **Schema tập trung** — Tất cả DB migrations ở `database/postgres/migrations/`, KHÔNG đặt trong từng service.
2. **Migration trước, code sau** — Thay đổi DB → tạo migration → review → apply → viết code.

---

### `models/` — AI Models

```
models/
├── yolo/                       # YOLOv8 weights (.pt, .engine)
├── reid/                       # ReID model weights
├── tensorrt/                   # Converted TensorRT engines
├── checkpoints/                # Training checkpoints
├── configs/                    # Model configs (yolov8n.yaml, osnet_x025.yaml)
├── scripts/                    # Export/convert scripts
│   ├── export_yolov8.py        #   PyTorch → ONNX → TensorRT
│   ├── export_reid.py          #   ReID model export
│   └── benchmark_models.py     #   Performance benchmarking
└── README.md                   # Model documentation
```

**RULE:** Model files (.engine, .onnx, .pt, .trt) KHÔNG commit git. Dùng scripts để generate trên target machine.

---

### `datasets/` — Training & Evaluation Data

```
datasets/
├── raw/                        # Raw collected data
├── processed/                  # Preprocessed data
├── annotations/                # Labels (COCO, YOLO format)
├── training/                   # Training splits
├── validation/                 # Validation splits
└── README.md                   # Dataset documentation
```

---

### `monitoring/` — Observability Stack

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Scrape targets
│   └── rules/                  # Alert + recording rules
├── grafana/
│   └── provisioning/
│       ├── datasources/        # Auto-provision Prometheus, Loki, Tempo
│       └── dashboards/         # Pre-built dashboards (system, AI pipeline)
├── loki/                       # Log aggregation config
├── tempo/                      # Distributed tracing config
└── alertmanager/               # Alert routing config
```

**RULE:** Mọi service PHẢI expose `/metrics` cho Prometheus. KHÔNG deploy mà không có monitoring.

---

### `infrastructure/` — DevOps & Deployment

```
infrastructure/
├── docker/                     # Shared Docker configs
├── kubernetes/
│   ├── base/                   # Kustomize base manifests
│   └── overlays/
│       ├── staging/            # Staging overrides
│       └── production/         # Production: HA, HPA, resource limits
├── nginx/                      # Reverse proxy configs
├── terraform/                  # Cloud IaC
├── ansible/                    # Config management
└── helm/                       # Helm charts
```

---

### `tests/` — Root-level Test Suites

```
tests/
├── integration/                # Cross-service integration tests
│   ├── test_ai_to_kafka.py     #   AI pipeline → Kafka message delivery
│   ├── test_kafka_to_analytics.py  #   Kafka → Analytics service processing
│   └── test_search_pipeline.py #   Image → Embedding → Vector search
├── e2e/                        # End-to-end flow tests
│   ├── test_full_tracking_flow.py  #   Camera → AI → Kafka → DB → UI
│   └── test_person_search.py   #   Upload image → Get results
├── load/                       # Load testing (Locust)
├── stress/                     # Stress testing (multi-stream GPU)
└── performance/                # Performance benchmarks
```

---

### `docs/` — Documentation Hub

```
docs/
├── architecture/               # System design documents
│   ├── system-overview.md      #   High-level architecture
│   ├── data-flow.md            #   Data flow diagrams
│   └── service-communication.md #  Inter-service protocols
├── api/                        # API documentation
├── deployment/                 # Deploy guides (Docker, K8s, GPU)
├── benchmark/                  # Performance benchmarks
├── erd/                        # Database schema diagrams
├── sequence/                   # Sequence diagrams (tracking, search)
├── diagrams/                   # Architecture diagrams
├── decisions/                  # ── ARCHITECTURE DECISION RECORDS ──
│   ├── 001-use-deepstream.md   #   Why DeepStream over custom pipeline
│   ├── 002-qdrant-over-milvus.md   #   Why Qdrant for vector search
│   ├── 003-event-driven-architecture.md
│   └── template.md             #   ADR template for new decisions
└── meeting-notes/              # Meeting notes archive
```

---

## Quy tắc phát triển (Development Rules)

### 1. Data Flow bắt buộc

```
Camera (RTSP) → ai-service (DeepStream)
                    ↓ Kafka "tracking-events"
               analytics-service (consumer)
                    ↓ Write
            PostgreSQL + Qdrant + MinIO
                    ↓ Kafka "notification-events"
               notification-service
                    ↓ WebSocket
               gateway → web (React)
```

**RULE: KHÔNG BAO GIỜ bypass Kafka.** AI service KHÔNG gọi database trực tiếp.

### 2. Service Communication

| From → To | Protocol | Khi nào |
|:-----------|:---------|:--------|
| web → gateway | HTTP/WS | Mọi API calls |
| gateway → services | HTTP/gRPC | Synchronous requests |
| ai-service → analytics | **Kafka** | Async tracking events |
| analytics → notification | **Kafka** | Async alert events |
| services → databases | TCP | Direct connections |

### 3. Branch Strategy

```
main           ← Production releases (protected, tag-based)
├── develop    ← Integration branch (staging auto-deploy)
├── feature/*  ← Feature branches (PR → develop)
├── fix/*      ← Bug fix branches
└── hotfix/*   ← Emergency fixes (PR → main)
```

### 4. Commit Convention

```
<type>(<scope>): <description>

feat(ai-service): add ByteTrack tracker support
fix(gateway): fix WebSocket reconnection race condition
docs(decisions): add ADR for event sourcing
```

Types: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `ci` · `chore`

### 5. Testing Requirements

| Level | Tool | Where | Coverage |
|:------|:-----|:------|:---------|
| Unit | pytest / Vitest | `apps/*/tests/` | ≥ 80% |
| Integration | pytest | `tests/integration/` | Critical paths |
| E2E | Playwright | `tests/e2e/` | Core flows |
| Load | Locust | `tests/load/` | Before release |
| Stress | Custom | `tests/stress/` | GPU capacity |

### 6. Tech Stack

| Layer | Technology | Version |
|:------|:-----------|:--------|
| **AI** | NVIDIA DeepStream | 7.x |
| **AI** | TensorRT, Triton | 10.x, 24.x |
| **Detection** | YOLOv8n/s | ultralytics |
| **ReID** | OSNet-x0.25 | torchreid |
| **Backend** | FastAPI | ≥0.115 |
| **ORM** | SQLAlchemy | ≥2.0 async |
| **Frontend** | React + TypeScript + Vite | 18+ |
| **State** | Zustand + TanStack Query | 4.x, 5.x |
| **DB** | PostgreSQL | 16 |
| **Vector DB** | Qdrant | 1.12+ |
| **Cache** | Redis | 7 |
| **Storage** | MinIO | latest |
| **Messaging** | Apache Kafka | 3.7+ |
| **Monitoring** | Prometheus + Grafana + Loki + Tempo | latest |
| **DevOps** | Docker + Kubernetes | 27+, 1.30+ |
| **CI/CD** | GitHub Actions | — |

---

> **Cập nhật lần cuối:** 2026-07-15 · **Version:** 2.0 (Enterprise Restructure)
