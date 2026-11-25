# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MATRIX_DATA_DIR=/data

WORKDIR /app

RUN useradd -m -u 10001 matrixuser && mkdir -p /data && chown -R matrixuser:matrixuser /data /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY a2a_shared_core.py matrix_live_harvesters.py ./
COPY 06-listingshield ./06-listingshield
COPY 07-siliconorigin ./07-siliconorigin
COPY 08-demurrage-audit ./08-demurrage-audit
COPY 09-saasbench ./09-saasbench
COPY wave2-matrix-quad-release/matrix_cloud_server.py ./wave2-matrix-quad-release/matrix_cloud_server.py

RUN chown -R matrixuser:matrixuser /app /data

USER matrixuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4)"

CMD ["python3", "wave2-matrix-quad-release/matrix_cloud_server.py"]
