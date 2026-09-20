# CyberSathi backend — fully offline, no API keys.
# The models are trained during the build so the running container needs no network at all.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY ml_training ./ml_training
COPY tests ./tests
COPY alembic.ini ./
COPY alembic ./alembic
COPY docker-entrypoint.sh ./

# Synthetic datasets -> trained text + URL models, baked into the image.
# Deterministic and offline: no dataset download, no API key.
RUN python ml_training/generate_datasets.py \
 && python ml_training/train_text_model.py \
 && python ml_training/train_url_model.py

RUN chmod +x docker-entrypoint.sh \
 && useradd --create-home --uid 10001 sathi \
 && mkdir -p /data \
 && chown -R sathi:sathi /app /data
USER sathi

# Keep the SQLite file on a volume so the seeded cohort survives a rebuild.
ENV DATABASE_URL=sqlite:////data/cybersathi.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).status==200 else 1)"

CMD ["./docker-entrypoint.sh"]
