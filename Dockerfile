# Multi-stage Dockerfile pour WaterBill API
# Stage 1: Builder - Installation des dépendances avec outils de build
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Installer les outils de build et dépendances système (optimisé)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Créer un environnement virtuel Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier et installer les dépendances Python (cache optimisé)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip check

# Stage 2: Runtime - Image finale optimisée
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Installer uniquement les dépendances runtime (sans outils de build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    libpq5 \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier l'environnement virtuel depuis le stage builder
COPY --from=builder /opt/venv /opt/venv

# Copier le projet (optimisé avec .dockerignore)
COPY . /app

# Créer un user non-root et définir les permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Exposé pour gunicorn/devserver
EXPOSE 8000

# Entrypoint (gère wait-for-db + migrate + collectstatic + lancement)
# ENTRYPOINT ["/bin/bash", "docker/entrypoint.sh"]
ENTRYPOINT ["/bin/bash", "/app/docker/entrypoint.sh"]
