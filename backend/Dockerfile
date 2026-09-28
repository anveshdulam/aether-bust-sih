FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TORCH_NUM_THREADS=1

WORKDIR /app

# libexpat/libgomp/curl are needed by netCDF4, torch and the compose healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libexpat1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY data ./data
COPY pyproject.toml ./

RUN mkdir -p /app/artifacts

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
