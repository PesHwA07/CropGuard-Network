# CropGuard Network — Architecture

## System Overview

```
                    ┌──────────────────────┐
                    │   Farmer Frontend     │
                    │ (React, mobile-first) │
                    └──────────┬────────────┘
                               │ REST (FastAPI, Swagger docs)
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend     │
                    │ (auth, CRUD, MCP)     │
                    └──────────┬────────────┘
                ┌──────────────┼───────────────┐
                ▼              ▼               ▼
        ┌───────────┐  ┌─────────────┐  ┌─────────────┐
        │  YOLOv8    │  │   Kafka     │  │  MongoDB    │
        │ Inference  │  │ (streaming) │  │ (reviews)   │
        │ (5 crops)  │  │             │  │             │
        └───────────┘  └──────┬──────┘  └─────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  PySpark             │
                    │ (regional aggregation│
                    │  + feature eng.)     │
                    └──────────┬────────────┘
                               ▼
                    ┌──────────────────────┐
                    │  Outbreak Forecasting │
                    │  Model + MLflow       │
                    └──────────────────────┘

                    ┌──────────────────────┐
                    │  RAG Advisory Service │
                    │ ChromaDB → Cross-     │
                    │ Encoder → Llama 3.3   │
                    └──────────────────────┘
```

## Regional Scope

- **District:** Chhatrapati Sambhajinagar (formerly Aurangabad), Maharashtra
- **Anchor taluka:** Paithan — Godavari river basin, supports both rainfed (Cotton, Jowar, Maize) and irrigated (Sugarcane) crops
- **Heatmap coverage:** 10 talukas within the district
- **Secondary district:** Jalna (adjacent, shared cropping patterns)

## Data Flow

### 1. Diagnosis Pipeline
```
Farmer uploads photo (with crop_type)
  → Image validation (type, size, sanitization)
  → YOLOv8 inference (crop-specific model loaded from MLflow)
  → Bounding-box detection + disease classification
  → Cause analysis lookup (per crop × disease)
  → Result stored in PostgreSQL (disease_reports)
  → Event published to Kafka (crop-disease-reports topic)
```

### 2. Regional Aggregation Pipeline
```
Kafka consumer reads crop-disease-reports
  → Aggregates by taluka × crop_type × disease
  → Rolling counts, threshold monitoring
  → If threshold breached → publish to outbreak-alerts topic
  → Heatmap endpoint serves aggregated data
```

### 3. Batch Forecasting Pipeline
```
PySpark reads historical disease/yield data
  → Feature engineering (seasonality, rainfall, neighbor-taluka spread lag)
  → Train outbreak forecasting model (XGBoost)
  → Model registered in MLflow
  → Served via /api/outbreak/district/{taluka_id}
```

### 4. RAG Advisory Pipeline
```
User query (e.g., "What fungicide for maize common rust?")
  → Dense similarity search in ChromaDB → top-20 chunks
  → Cross-encoder reranker → top-5 (crop + severity aware)
  → Llama 3.3 70B Versatile generates grounded answer with citations
  → Safety guardrails validate pesticide dosage claims
```

## Storage

| Store | Purpose | Key Collections/Tables |
|-------|---------|----------------------|
| PostgreSQL | Structured data | `farmers`, `disease_reports`, `shop_stock` |
| MongoDB | Unstructured data | `solution_reviews` |
| ChromaDB | Vector store (RAG) | Advisory document embeddings |
| Azure Blob | Image storage | Uploaded crop photos |
| MLflow | Model registry | YOLOv8 models (per crop), forecast model |

## Kafka Topics

| Topic | Partitions | Producer | Consumer |
|-------|-----------|----------|----------|
| `crop-disease-reports` | 3 | Diagnosis API | Regional aggregation, Spark ingestion |
| `outbreak-alerts` | 1 | Forecasting service | Dashboard, notification service |

## Authentication

Three roles via JWT claims:
- **Farmer** — upload photos, view diagnoses, submit reviews, query advisory
- **Shop Owner** — update own shop stock only
- **Extension Officer** — view heatmap, aggregated data, query advisory

Enforced via `require_role()` FastAPI dependency per route.

## Deployment

- **Local:** Docker Compose (all services)
- **Demo:** Azure App Service (free F1) + Azure Blob Storage
- **CI/CD:** GitHub Actions — lint, test, Docker build
