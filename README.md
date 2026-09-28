# AETHER-BUST (SIH26079)

Operational Console for Meteorologists to detect and analyze NWP Forecast Busts using Deep Learning.

## Running the Application

This application is fully dockerized. To start the entire stack:

```bash
docker compose up -d --build
```

### Services

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **MongoDB**: localhost:27017

### Health endpoints

- **Backend Health**: http://localhost:8000/health
- **Backend API Docs**: http://localhost:8000/docs
