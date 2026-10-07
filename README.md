# 🌩️ AETHER-BUST
**An AI console that predicts when and where weather forecast models will fail, and explains why.**

[📄 SIH presentation](AETHER-BUST_SIH2026_SMART_AUTOMATION.pdf)

## SIH 2026 Details
| | |
|---|---|
| Problem Statement ID | SIH26079 |
| Problem Statement Title | AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts |
| Organization / Ministry | Ministry of Earth Sciences (MoES) |
| Theme / Category | Smart Automation / Software |
| Team Name / ID | TechBytes / 128249 |
| Institution | VIT Bhopal University, Sehore |

## ⚡ For Judges: 2-Minute Overview
- **Problem:** Medium-range weather forecasts (GFS/ECMWF) occasionally fail spectacularly ("busts"). These unpredicted failures catch disaster agencies off guard, leading to poor emergency response.
- **Solution:** AETHER-BUST is an AI layer that runs alongside traditional NWP models. It predicts the probability of a forecast bust, the expected error magnitude, and uses XAI to explain which atmospheric variables are driving the failure.
- **Run it:** `git clone https://github.com/anveshdulam/aether-bust-sih.git && cd aether-bust-sih && cp .env.example .env && docker compose up --build` → http://localhost:5173
- **Where to look:** Open the map → Select the 'Bust' layer → Click any flagged point → View the XAI attribution panel → Ask the AETHER chatbot for a deeper analysis.

## ✅ What's Real vs Simulated
| Component | Status |
|---|---|
| BustNet architecture (U-Net + ConvLSTM) | Implemented |
| Data pipeline (GFS/ERA5 downloaders) | Implemented, tested on local environments |
| Training data | 4 Years of Historical Real Data (Continuous ERA5/GFS, 2019-2022) |
| Model weights | Trained on Real Data |
| Integrated Gradients attribution | Implemented |
| Dashboard, API, chatbot | Implemented |
| Validation on held-out real busts | In progress: [train 2019–2021 / test 2022] |

## Problem & Why Existing Approaches Fall Short
**What is a "Bust"?** A forecast bust is defined as a scenario where a deterministic weather model (like GFS) deviates from the actual ground truth (like ERA5 reanalysis) by a catastrophic margin. In this system, a bust occurs when the predicted variable's error exceeds the 90th percentile of historical errors.

Ensemble forecast spread indicates general uncertainty, but fails to definitively predict *where* and *why* a specific deterministic forecast will bust. While new AI weather models (like Pangu-Weather) predict the weather itself, they don't predict the *failures* of operational numerical models.

## Solution Overview
AETHER-BUST frames the problem as an image-to-image translation task. 

1. **Input:** GFS forecasts and atmospheric variables are passed into a Deep Learning architecture.
2. **Model (BustNet):** A hybrid U-Net + ConvLSTM network processes spatial and temporal relationships.
3. **Output:** The model outputs a Bust Probability Map (0-100%) and an Error Magnitude Map.
4. **XAI:** Integrated Gradients mathematically attributes the bust prediction back to the original input variables, providing meteorologists with trust and explainability.

## Key Features
| Feature | Description |
|---|---|
| **Bust Probability Heatmap** | 10-day lead time spatial mapping of forecast failure risks. |
| **Error Magnitude Estimation** | Predicts the severity of the bust (e.g., geopotential height error). |
| **XAI Attribution** | Integrated Gradients pinpoints the driving variables (e.g., humidity, wind). |
| **AETHER Chatbot** | An AI Analyst (Gemini) that reads the current map state to answer meteorological questions. |

## Keyboard Shortcuts
| Key | Action |
|---|---|
| `Left Arrow` | Step backward in time (decrease lead time) |
| `Right Arrow` | Step forward in time (increase lead time) |
| `C` | Toggle Compare Mode (Baseline Error Overlay) |
| `Escape` | Deselect region and close XAI attribution panel |

## Screenshots / GIFs
*(To be added by team)*

## Tech Stack
- **Frontend:** React 18, Node 18+, TypeScript, Vite, Tailwind CSS, Zustand, Deck.gl, Leaflet
- **Backend:** Python 3.11, FastAPI, PyTorch, Captum (XAI), Motor (Async MongoDB), xarray
- **Database:** MongoDB
- **AI Integration:** Google Gemini API (AETHER Chatbot)
- **Deployment:** Docker, Docker Compose

## Getting Started
**Prerequisites:** Docker ≥ 24.0, 8+ GB RAM, ports 5173/8000/27017 free. Python 3.11+ and Node.js 18+ for local dev.

1. Clone the repository: `git clone https://github.com/anveshdulam/aether-bust-sih.git`
2. Configure environment: `cp .env.example .env` (Set `GEMINI_API_KEY` for the chatbot. The app will run without it, but the chatbot will be disabled).
3. Start the stack: `docker compose up -d --build`
4. Open the dashboard at `http://localhost:5173`

**Run without Docker (Local Dev):**
- **Backend:** `cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app --reload`
- **Frontend:** `cd frontend && npm install && npm run dev`

**Troubleshooting:**
- *MongoDB Connection Error:* Ensure MongoDB is running locally on port 27017 if running without Docker.
- *Solid Color Map Issue:* Clear `backend/artifacts` to remove stale predictions when switching model weights.

## Environment Variables
| Variable | Purpose | Required |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | Yes |
| `MODEL_WEIGHTS_PATH` | Path to PyTorch `.pt` weights | Yes (Weights are included in repo at `backend/app/ml/weights/bustnet_real_4years.pt`) |
| `GEMINI_API_KEY` | API key for the AETHER Chatbot | No (Chatbot disabled without it) |
| `CDSAPI_KEY` | Copernicus API Key for historical data | No (For training only) |

## API Reference
| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/forecast-runs` | GET | List available model runs |
| `/api/v1/bust/tiles/{z}/{x}/{y}` | GET | Fetch vector tiles for probability/error maps |
| `/api/v1/attribution` | GET | Get XAI Integrated Gradients attribution for a coordinate |
| `/api/v1/chat` | POST | Stream responses from the AETHER AI Chatbot |

## Evaluation Plan
| Metric | Purpose | Result |
|---|---|---|
| Training / validation MSE | Convergence | Validated (Converged to 0.0217) |
| AUROC | Bust classification | Planned |
| Brier score | Probability calibration | Planned |
| MAE / RMSE | Error-magnitude accuracy | Planned |
| Inference latency | Feasibility | GPU-accelerated (<1.5s on RTX 6000 for one 10-day run) |

## SIH Evaluation Criteria
- **Innovation:** Predicting the *failure* of models rather than predicting the weather itself. Applying XAI (Integrated Gradients) to meteorology.
- **Feasibility:** Utilizes public operational data (GFS/ERA5) and runs on standard commodity hardware.
- **Scalability:** Built on a tiled vector approach (Deck.gl/FastAPI) allowing scaling from regional 128×128 grids to global high-resolution domains.
- **Impact:** Empowers disaster management agencies to prepare alternative plans when operational forecasts are flagged as unreliable.
- **Responsible AI:** Acts as a "human-in-the-loop" warning system. It is not a replacement for official forecasts, but a tool to quantify their reliability.

## Limitations
- False alarm rates and misses need rigorous quantification across decadal datasets.
- Current weights are regional and trained on 4 years of extreme weather data; global generalizability requires further training.

## Roadmap
- Integrate ECMWF operational forecasts alongside GFS.
- Expand spatial domain to full global coverage.
- Add temporal feature tracking for cyclone trajectory bust analysis.

## Team
- **Dulam Anvesh Goud** · Team Leader / Backend & ML
- **Mummadi Nageshwar Reddy** · ML Engineer
- **Yatham Jathindra Reddy** · Frontend Developer
- **Nomaan Ahmed** · Data Engineer
- **Kirti** · UI/UX Designer
- **Kashish Hasani** · DevOps & Testing

## Data Sources & Acknowledgements
- ERA5 (Copernicus Climate Change Service / ECMWF)
- NOAA GFS
- Built using PyTorch, FastAPI, and React.
- Contains modified Copernicus Climate Change Service information [2026].

## License
MIT License
