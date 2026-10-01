FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TORCH_NUM_THREADS=1

WORKDIR /app

# libeccodes is required for cfgrib to read GRIB2 files
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libexpat1 libgomp1 libeccodes-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY app ./app
COPY data ./data
COPY pyproject.toml ./

RUN mkdir -p /app/artifacts

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
