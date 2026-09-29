# 🌩️ AETHER-BUST: Meteorological Forecast Failure Prediction System

> An operational AI console that predicts medium-range weather forecast failures. 
> Using spatiotemporal deep learning on GFS/ECMWF data, it provides localized bust 
> probabilities, error magnitudes, and Explainable AI to identify the exact atmospheric drivers.

[![SIH 2026](https://img.shields.io/badge/SIH-2026-blue)](https://sih.gov.in)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch-orange)](https://pytorch.org)
[![React](https://img.shields.io/badge/Frontend-React_18-cyan)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

### 🎯 Smart India Hackathon 2026

**Theme:** Disaster Management  
**Team Name:** TechBytes  
**Team ID:** 128249  
**Institution:** VIT Bhopal University, Sehore  

---

## 🎯 Problem Statement

Numerical Weather Prediction (NWP) models like **GFS** and **ECMWF** are the backbone of global meteorology. However, these models sometimes suffer from **"Forecast Busts"**—severe, localized prediction failures where the model's physics fail to capture complex atmospheric dynamics (like unexpected cyclogenesis or massive Himalayan orographic lift).

When these models bust, disaster management agencies are caught completely off guard. 
This creates:
- ❌ Catastrophic socioeconomic damage
- ❌ Unprepared emergency response teams
- ❌ Loss of life due to unexpected severe weather
- ❌ Reduced public trust in meteorological forecasts

### Our Objective
Instead of building a new weather model from scratch, our objective is to develop an intelligent system that:
1. Predicts **when and where** existing NWP models will fail 1 to 10 days in advance.
2. Quantifies the **expected error magnitude**.
3. Explains **why** the model is failing using Explainable AI (XAI).

---

## 💡 Solution Overview

**AETHER-BUST** is a mission-critical, interactive operational console designed for meteorologists. It acts as an intelligence layer on top of existing NWP outputs.

        Raw GFS / ECMWF Data (10 Channels)
                  │
                  ▼
        ┌───────────────────┐
        │ 5D Tensor Builder │
        └─────────┬─────────┘
                  ▼
        ┌───────────────────┐
        │ BustNet Model     │
        │ (U-Net+ConvLSTM)  │
        └─────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    Bust Probability    Expected Error
        Map                 Magnitude
                  │
                  ▼
        ┌───────────────────┐
        │ Explainable AI    │
        │ (Captum / IG)     │
        └─────────┬─────────┘
                  ▼
        Meteorologist Dashboard (WebGL)

---

## ⭐ Key Features

| Feature | Description |
|---|---|
| 🔮 Spatiotemporal Prediction | Analyzes 10 meteorological channels across 10 future days to predict busts |
| 🧠 Deep Learning Architecture | Custom U-Net + ConvLSTM with Temporal Attention |
| 🔍 Explainable AI (XAI) | Uses Integrated Gradients to show *why* a forecast is failing |
| 🗺️ WebGL Digital Twin | High-performance hardware-accelerated map rendering via Deck.gl |
| 📊 Real-Time Telemetry | Interactive scrubbers and bounding-box risk isolation |
| ⚡ GPU-Optimized | PyTorch inference engine designed for rapid batch processing |

---

## 🧠 AI/ML Pipeline

### Step 1 — Data Ingestion
10 meteorological channels (Temperature, Precipitation, Geopotential Height, Wind Shear, CAPE, etc.) across 10 forecast days are downloaded via CDS/GFS APIs.

### Step 2 — Tensor Materialization
Data is regridded, normalized, and spatiotemporally aligned into 5D Tensors: `[Batch, Time, Channels, Height, Width]`.

### Step 3 — Spatiotemporal Inference
Tensors are passed into `BustNet`. The network learns both spatial meteorological patterns (U-Net) and their temporal evolution over the 10-day forecast horizon (ConvLSTM).

### Step 4 — XAI Driver Attribution
For any predicted "bust", the system runs Integrated Gradients (Captum) backwards through the network to identify which input channels (e.g., Deep Layer Shear, CAPE) contributed most to the prediction.

---

## 📊 Dataset & Data Strategy

### Primary Datasets
- **ERA5 Reanalysis (ECMWF)**: Ground truth atmospheric data.
- **GFS Historical Forecasts (NOAA)**: The predictions we are evaluating.

### Synthetic Data Generator (For Prototyping)
Because downloading and processing 10 years of global GFS/ERA5 GRIB2 files requires terabytes of storage and weeks of processing, we developed a **Physics-Aware Synthetic Generator** for rapid prototyping and UI development.

The generator creates physically consistent 5D tensors with simulated localized "busts" driven by synoptic variables (e.g., elevated CAPE and Wind Shear), allowing us to validate the end-to-end pipeline and XAI systems locally.

> ⚠️ Note: The synthetic data generation is explicitly identified as simulated data and is used strictly to validate the operational software architecture without requiring an HPC cluster.

---

## 🧪 Model Details

### Model Architecture
**BustNet**: A hybrid `U-Net` + `ConvLSTM` architecture.
- **U-Net**: Extracts multi-scale spatial features (synoptic scale down to mesoscale).
- **ConvLSTM**: Models the temporal evolution of the atmosphere over the 10-day lead time.

### Inputs
`[1, 10, 10, 128, 128]` 
*(Batch=1, Time=10 Days, Channels=10, Height=128, Width=128)*

### Outputs
1. **Bust Probability Map**: 0-100% likelihood of forecast failure.
2. **Error Magnitude Map**: Expected deviation from the forecast (e.g., ±5°C or ±20mm rainfall).

---

## 🏗️ System Architecture

Our system is broken into three core, decoupled microservices:

1. **Machine Learning Pipeline (PyTorch)**: A highly optimized PyTorch inference engine processing 5D atmospheric tensors.
2. **FastAPI Backend**: A highly concurrent API that handles model orchestration, geospatial bounding boxes, and connects to MongoDB.
3. **React + WebGL Frontend**: A real-time data visualization layer that renders complex NetCDF/JSON spatial data onto hardware-accelerated maps.

---

## 🛠️ Technology Stack

### Machine Learning
- Python 3.11
- PyTorch
- Captum (Integrated Gradients / XAI)
- NumPy, SciPy, xarray

### Backend
- FastAPI
- Uvicorn
- MongoDB (Geospatial `$geoWithin` indexing)

### Frontend
- React 18 (TypeScript)
- Vite
- TailwindCSS
- Zustand (State Management)
- Deck.gl / Leaflet (WebGL Map Rendering)

### Infrastructure
- Docker & Docker Compose

---

## 📂 Project Structure

```text
aether-bust-sih/
│
├── backend/
│   ├── app/
│   │   ├── ml/             # PyTorch Models & XAI
│   │   ├── routers/        # FastAPI Endpoints
│   │   └── services/       # Core Logic
│   ├── data/               # CDS/GFS Downloaders & Synthetic Generators
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/     # React Components (Map, UI)
│   │   ├── store/          # Zustand State
│   │   └── api/            # Backend Integrations
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Installation & Running

The fastest and most reliable way to run the entire AETHER-BUST stack is via Docker. The provided compose file spins up the Frontend, Backend, and MongoDB databases automatically.

### 1. Clone the Repository
```bash
git clone https://github.com/anveshdulam/aether-bust-sih.git
cd aether-bust-sih
```

### 2. Start the Stack (Docker)
```bash
docker compose up -d --build
```

### 3. Access the Services
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB**: `localhost:27017`

---

## 🔌 API Documentation

Once the backend is running, FastAPI automatically provides interactive Swagger documentation at `/docs`.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/runs/default` | GET | Initialize/Fetch the default ML run |
| `/api/v1/layers/bust` | POST | Fetch Bust Probability map layer |
| `/api/v1/attribution` | GET | Run XAI (Integrated Gradients) on a specific lat/lon |
| `/api/v1/export/data` | GET | Export region data as GeoJSON/NetCDF |

---

## ⚠️ Current Limitations

- **Model Training**: The current repository contains the full architecture, but weights must be trained on a high-performance GPU cluster (A100s) using actual ERA5/GFS archives before production deployment. The current demonstration uses untrained weights / synthetic physics to validate the pipeline.
- **Data Pipeline**: Downloading historical GRIB2 files from NOAA/ECMWF requires high bandwidth and preprocessing time. 
- **Geospatial Scope**: The current operational prototype focuses on a 128x128 grid (regional scale) for performance reasons.

---

## 🗺️ Roadmap

### Phase 1 — Prototype (SIH 2026)
- [x] Spatiotemporal architecture design
- [x] Synthetic physics data generator
- [x] XAI integration (Integrated Gradients)
- [x] WebGL Dashboard implementation
- [x] FastAPI Backend & E2E Pipeline

### Phase 2 — Training & Validation
- [ ] Ingest 10 years of GFS & ERA5 data
- [ ] Train `BustNet` on HPC GPU cluster
- [ ] Validate accuracy metrics (MAE, RMSE, AUROC) against historical busts

### Phase 3 — Production Deployment
- [ ] Integrate real-time operational GFS data streams
- [ ] Deploy to cloud infrastructure
- [ ] Setup automated alerting for meteorologists

---

## 👨‍💻 Team TechBytes

| Member | Role | 
|---|---|
| **DULAM ANVESH GOUD** | Team Leader |
| MUMMADI NAGESHWAR REDDY | Team Member |
| YATHAM JATHINDRA REDDY | Team Member |
| NOMAAN AHMED | Team Member |
| KIRTI | Team Member |
| KASHISH HASANI | Team Member |

---

## 📜 License

This project is developed for the Smart India Hackathon (SIH) 2026.
