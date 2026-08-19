# CropGuard Network

Crop disease detection and regional outbreak advisory platform for Chhatrapati Sambhajinagar district, Maharashtra — anchored at Paithan taluka.

Farmers upload crop photos for instant YOLOv8-based diagnosis (bounding-box localization, not just classification), while every report feeds a live district-level disease-spread heatmap, outbreak forecasting, and a RAG-powered advisory assistant.

## Target Crops (v1)

| Crop | Dataset | Classes |
|------|---------|---------|
| Maize | PlantVillage Corn | Healthy, Common Rust, Gray Leaf Spot, N. Leaf Blight |
| Soybean | SoyNet (Indian fields) | Healthy, Diseased |
| Sugarcane | Mendeley Maharashtra-specific | Healthy, Mosaic, Red Rot, Rust, Yellow |
| Cotton | Kaggle Cotton Disease | Healthy, Bacterial Blight, Curl Virus, Fusarium Wilt |
| Wheat | Kaggle Wheat Leaf | Healthy, Rust |

## Tech Stack

**Backend:** FastAPI · PostgreSQL · MongoDB · Kafka · PySpark  
**CV:** YOLOv8 (Ultralytics) · MLflow  
**RAG:** ChromaDB · Cross-encoder reranker · Groq (Llama 3.3 70B)  
**Frontend:** React (Vite) · Leaflet (OpenStreetMap)  
**Deploy:** Docker Compose · Azure (demo)

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd CropGuard-Network

# 2. Copy env template
cp .env.example .env

# 3. Start infrastructure
cd infra
docker-compose up -d

# 4. Verify services
docker-compose ps
```

Services started:
- **PostgreSQL** — localhost:5432
- **MongoDB** — localhost:27017
- **Kafka** — localhost:9092
- **MLflow** — http://localhost:5000

## Project Structure

```
├── backend/          # FastAPI app, routers, auth, Kafka, vision inference
├── frontend/         # React (Vite), Leaflet map, mobile-first UI
├── vision_training/  # YOLOv8 training scripts, augmentation, evaluation
├── spark_jobs/       # PySpark ingestion, feature engineering, forecasting
├── rag_service/      # Retriever, cross-encoder reranker, LLM generator
├── infra/            # Docker Compose, Dockerfiles, seed data
├── postman/          # API test collection
├── docs/             # Architecture documentation
└── .github/          # CI/CD workflows
```

## Region

**District:** Chhatrapati Sambhajinagar (formerly Aurangabad), Maharashtra  
**Anchor taluka:** Paithan (Godavari river basin — rainfed + irrigated)  
**Heatmap talukas (10):** Chh. Sambhajinagar, Paithan, Kannad, Khuldabad, Sillod, Phulambri, Soegaon, Vaijapur, Gangapur, and surrounding area  
**Secondary:** Jalna district (adjacent, shared cropping patterns)

## License

MIT
