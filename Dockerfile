FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion/ ./ingestion/
COPY rules_engine/ ./rules_engine/
COPY data/ ./data/

# This container expects these environment variables (via docker run -e
# or a Kubernetes ConfigMap): CSV_PATH, GMS_SERVER, DRY_RUN

CMD ["python", "-m", "ingestion.run_ingestion", "--dry-run"]