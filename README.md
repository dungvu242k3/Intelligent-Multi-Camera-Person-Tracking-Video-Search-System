# 🎯 Intelligent Multi-Camera Person Tracking & Video Search System

Production-grade, multi-camera person tracking system powered by **NVIDIA DeepStream**, featuring real-time cross-camera person re-identification (ReID), intelligent video search, and a comprehensive monitoring dashboard.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        React Dashboard                          │
│              (Live Monitor · Search · Analytics)                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │  HTTP / WebSocket
┌───────────────────────────▼──────────────────────────────────────┐
│                     API Gateway (Nginx/Traefik)                  │
└───────┬──────────┬──────────────┬────────────┬───────────────────┘
        │          │              │            │
   ┌────▼───┐ ┌───▼────┐  ┌─────▼────┐ ┌─────▼─────┐
   │  API   │ │ Camera │  │  Search  │ │  Alert    │
   │Service │ │Manager │  │ Service  │ │ Service   │
   └────┬───┘ └───┬────┘  └─────┬────┘ └─────┬─────┘
        │         │              │            │
        └─────────┼──────────────┼────────────┘
                  │         ┌────▼────┐
            ┌─────▼─────┐  │  Qdrant │
            │   Kafka    │  │(Vector) │
            └─────┬─────┘  └─────────┘
                  │
      ┌───────────▼───────────────┐
      │   DeepStream AI Pipeline  │
      │  ┌─────┐ ┌─────┐ ┌─────┐ │
      │  │Detect│→│Track│→│ReID │ │
      │  └─────┘ └─────┘ └─────┘ │
      └───────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|:------|:-----------|
| **AI Pipeline** | NVIDIA DeepStream 7.x, TensorRT, Triton Inference Server |
| **Detection** | YOLOv8/v10 (TensorRT optimized) |
| **Tracking** | NvDCF / ByteTrack + Custom MTMC Association |
| **ReID** | OSNet-x1.0 / BoT-S50 |
| **Backend** | FastAPI (Python 3.11+), Celery, gRPC |
| **Frontend** | React 18, TypeScript, Vite, Zustand |
| **Databases** | PostgreSQL 16, Qdrant, Redis 7, MinIO |
| **Messaging** | Apache Kafka |
| **Monitoring** | Prometheus, Grafana, Loki, Jaeger |
| **DevOps** | Docker, Kubernetes, GitHub Actions |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- NVIDIA GPU with drivers 535+
- NVIDIA Container Toolkit
- Node.js 20+ (frontend development)
- Python 3.11+ (backend development)

### Development Setup

```bash
# 1. Clone & configure
git clone <repo-url>
cd Intelligent-Multi-Camera-Person-Tracking-Video-Search-System
cp .env.example .env

# 2. Start all services
make dev-up

# 3. Access services
#    Frontend:    http://localhost:5173
#    Backend API: http://localhost:8000/docs
#    Grafana:     http://localhost:3001
#    MinIO:       http://localhost:9001
```

### Useful Commands

```bash
make dev-up          # Start dev environment
make dev-down        # Stop dev environment
make dev-logs        # View logs
make test            # Run all tests
make lint            # Run linters
make build           # Build production images
make migrate         # Run database migrations
```

## 📁 Project Structure

```
├── ai-pipeline/       # DeepStream AI Engine (detection, tracking, ReID)
├── backend/           # FastAPI backend services
├── frontend/          # React dashboard
├── infra/             # K8s manifests, Terraform, monitoring configs
├── shared/            # Protobuf definitions, Kafka schemas
├── docs/              # Architecture & API documentation
└── scripts/           # Development & deployment scripts
```

## 📊 Key Features

- **Real-time Multi-Camera Tracking**: Track persons across 30-100+ cameras simultaneously
- **Cross-Camera Re-Identification**: Maintain consistent person IDs across camera views
- **Intelligent Search**: Search by image upload or text description
- **Live Dashboard**: Multi-camera grid view with real-time tracking overlay
- **Alert System**: Configurable alerts for person detection events
- **Analytics**: Heatmaps, traffic flow, dwell time analysis
- **Full Observability**: Metrics, logs, and distributed tracing

## 📖 Documentation

- [Architecture Guide](docs/architecture.md)
- [API Specification](docs/api-spec.md)
- [Deployment Guide](docs/deployment.md)

## 📄 License

This project is proprietary. All rights reserved.
