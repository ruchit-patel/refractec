# =============================================================================
# Multi-stage Dockerfile for Frappe 16 + Refractec
# Based on official frappe_docker patterns
# =============================================================================

# --------------- Stage 1: Build assets ---------------
FROM python:3.14-slim-bookworm AS assets-builder

ARG FRAPPE_BRANCH=version-16
ARG REFRACTEC_REPO=https://github.com/ruchit-patel/refractec.git
ARG REFRACTEC_BRANCH=master
ARG DOPPIO_REPO=https://github.com/NagariaHussain/doppio.git
ARG DOPPIO_BRANCH=master

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    libmariadb-dev libmariadb-dev-compat \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 24 (required by Frappe 16)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Create bench user and directory
RUN useradd -ms /bin/bash frappe
WORKDIR /home/frappe

# Install bench CLI
RUN pip install --no-cache-dir frappe-bench

# Init bench with Frappe
USER frappe
RUN bench init --frappe-branch ${FRAPPE_BRANCH} --skip-redis-config-generation --no-backups frappe-bench

WORKDIR /home/frappe/frappe-bench

# Install apps
RUN bench get-app --branch ${REFRACTEC_BRANCH} ${REFRACTEC_REPO} \
    && bench get-app --branch ${DOPPIO_BRANCH} ${DOPPIO_REPO}

# Build frontend assets (JS/CSS bundles)
RUN bench build --app frappe \
    && bench build --app refractec

# Build the React frontend (supervisor mobile app)
WORKDIR /home/frappe/frappe-bench/apps/refractec/frontend
RUN npm ci && npm run build

WORKDIR /home/frappe/frappe-bench

# --------------- Stage 2: Production image ---------------
FROM python:3.14-slim-bookworm AS production

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    libmariadb3 \
    mariadb-client \
    wkhtmltopdf \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 24 (needed for socketio at runtime)
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create frappe user
RUN useradd -ms /bin/bash frappe
WORKDIR /home/frappe/frappe-bench

# Copy bench from builder
COPY --from=assets-builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

# Install bench CLI in production image
RUN pip install --no-cache-dir frappe-bench

# Copy entrypoint and production WSGI wrapper
COPY --chown=frappe:frappe docker/entrypoint.sh /entrypoint.sh
COPY --chown=frappe:frappe docker/wsgi.py /home/frappe/frappe-bench/wsgi.py
RUN chmod +x /entrypoint.sh

# Install gosu for stepping down from root in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

USER frappe

# Create required directories
RUN mkdir -p logs config

# Generate default configs (will be overridden by entrypoint)
RUN node -e "console.log('{}')" > sites/common_site_config.json

# Set SITES_PATH globally — Frappe reads this at module import time
ENV SITES_PATH=/home/frappe/frappe-bench/sites

EXPOSE 8000 9000

# Entrypoint runs as root to fix volume permissions, then drops to frappe
USER root
ENTRYPOINT ["/entrypoint.sh"]
CMD ["web"]
