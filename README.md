<div align="center">
  <img src="https://img.shields.io/badge/Smart_India_Hackathon-2026-orange?style=for-the-badge&logo=hackaday" alt="SIH 2026" />
  <img src="https://img.shields.io/badge/Status-Completed-success?style=for-the-badge" alt="Status" />
  
  <br />
  <br />

  <h1>🌩️ AETHER-BUST</h1>
  <p>
    <b>AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts</b>
  </p>
  
  <p>
    An operational AI console that predicts medium-range weather forecast failures. Using a spatiotemporal deep learning model (U-Net + ConvLSTM) on GFS/ECMWF data, it provides localized bust probabilities, error magnitudes, and Explainable AI (Grad-CAM/SHAP) to identify the exact atmospheric drivers causing the forecast to fail.
  </p>
</div>

<hr />

## 📖 Table of Contents
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Running the Application (Docker)](#-running-the-application-docker)
- [Manual Setup (Development)](#-manual-setup-development)

---

## 🌪️ The Problem
Numerical Weather Prediction (NWP) models like **GFS** and **ECMWF** are the backbone of global meteorology. However, these models sometimes suffer from **"Forecast Busts"**—severe, localized prediction failures where the model's physics fail to capture complex atmospheric dynamics (like unexpected cyclogenesis or massive Himalayan orographic lift).

When these models bust, disaster management agencies are caught completely off guard, leading to catastrophic socioeconomic damage and loss of life.

## 💡 Our Solution
**AETHER-BUST** is a mission-critical, interactive operational console designed for meteorologists. Instead of building a new weather model from scratch, we use **Spatiotemporal Deep Learning** to predict *when, where, and why* the existing NWP models will fail 1 to 10 days in advance.

By identifying high-risk failure zones early, agencies like the IMD (India Meteorological Department) and NDMA can manually intervene and issue targeted early warnings.

---

## ✨ Key Features

1. **Spatiotemporal Bust Prediction (Day 1-10)**
   - Utilizes a custom **U-Net + ConvLSTM** architecture with Temporal Attention to analyze 10 meteorological channels across 10 future days.
   - Outputs highly accurate localized bust probability maps and expected error magnitudes.

2. **Explainable AI (XAI)**
   - Avoids the "black box" AI problem. 
   - Implements **Grad-CAM** and **SHAP** to visually show meteorologists exactly *which* atmospheric drivers (e.g., Deep Layer Shear, CAPE, Moisture) are causing the forecast to fail.

3. **Premium Operational Dashboard**
   - Built on a strict "anti-cliché" aesthetic. Uses dark-mode **WebGL (Deck.gl / Leaflet)** rendering for high-performance tensor overlay visualization.
   - Interactive scrubbers, telemetry panels, and bounding-box risk isolation.

---

## 🏗️ System Architecture

Our system is broken into three core, decoupled microservices:

1. **Machine Learning Pipeline**: A highly optimized PyTorch inference engine processing 5D atmospheric tensors (`[Batch, Time, Channels, Height, Width]`).
2. **FastAPI Backend**: A highly concurrent API that handles model orchestration, geospatial bounding boxes, and connects to MongoDB for telemetry.
3. **React + WebGL Frontend**: A real-time data visualization layer that renders complex NetCDF/JSON spatial data onto hardware-accelerated maps.

---

## 🛠️ Technology Stack

| Category | Technology |
| :--- | :--- |
| **Deep Learning** | PyTorch, NumPy, SciPy, Captum (XAI) |
| **Backend API** | FastAPI, Pydantic, Uvicorn |
| **Database** | MongoDB (Geospatial `$geoWithin` indexing) |
| **Frontend UI** | React 18, TailwindCSS, Zustand |
| **Map Rendering** | Leaflet, Deck.gl, MapLibre standards |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Running the Application (Docker)

The fastest and most reliable way to run the entire AETHER-BUST stack is via Docker. The provided compose file spins up the Frontend, Backend, and MongoDB databases automatically.

```bash
# Clone the repository
git clone https://github.com/anveshdulam/aether-bust-sih.git
cd aether-bust-sih

# Start the stack using Docker Compose
docker compose up -d --build
```

**Services will be available at:**
- **Frontend Dashboard**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **MongoDB**: `localhost:27017`
- **Swagger API Docs**: `http://localhost:8000/docs`

---

## 💻 Manual Setup (Development)

If you wish to run the services natively without Docker for development purposes:

### 1. Database
Ensure MongoDB is running locally on port `27017`.
```bash
python scripts/seed_mongo.py
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 3. Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

---
<div align="center">
  <p><i>Developed with ❤️ for the Smart India Hackathon 2026</i></p>
</div>
