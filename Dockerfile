# =============================================================================
# Multi-stage Dockerfile for Frappe 16 + Refractec
# Based on official frappe_docker production Containerfile
# =============================================================================

ARG PYTHON_VERSION=3.14.2
ARG DEBIAN_BASE=bookworm
ARG NODE_VERSION=24.13.0

# --------------- Stage 1: Base image with runtime deps ---------------
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

ARG NODE_VERSION
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN useradd -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    git \
    nginx \
    gettext-base \
    file \
    # weasyprint
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    # MariaDB
    mariadb-client \
    less \
    # For healthcheck
    jq \
    # wkhtmltopdf
    wkhtmltopdf \
    xvfb \
    # For MIME type detection
    media-types \
    # NodeJS
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && rm -rf /var/lib/apt/lists/* \
    # nginx: remove default site, fix permissions for non-root
    && rm -f /etc/nginx/sites-enabled/default \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && touch /run/nginx.pid \
    && chown -R frappe:frappe /etc/nginx/conf.d \
    && chown -R frappe:frappe /etc/nginx/nginx.conf \
    && chown -R frappe:frappe /var/log/nginx \
    && chown -R frappe:frappe /var/lib/nginx \
    && chown -R frappe:frappe /run/nginx.pid \
    && pip install --no-cache-dir frappe-bench \
    && sed -i '/user www-data/d' /etc/nginx/nginx.conf

# Copy nginx config template and entrypoint
COPY docker/nginx/nginx-template.conf /templates/nginx/frappe.conf.template
COPY docker/nginx/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh
RUN chmod +x /usr/local/bin/nginx-entrypoint.sh

# --------------- Stage 2: Build deps ---------------
FROM base AS build

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    build-essential \
    gcc \
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    pkg-config \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER frappe

# --------------- Stage 3: Build bench + apps ---------------
FROM build AS builder

ARG FRAPPE_BRANCH=version-16
ARG FRAPPE_PATH=https://github.com/frappe/frappe
ARG REFRACTEC_REPO=https://github.com/ruchit-patel/refractec.git
ARG REFRACTEC_BRANCH=master
ARG DOPPIO_REPO=https://github.com/NagariaHussain/doppio.git
ARG DOPPIO_BRANCH=master

RUN bench init \
    --frappe-branch=${FRAPPE_BRANCH} \
    --frappe-path=${FRAPPE_PATH} \
    --no-procfile \
    --no-backups \
    --skip-redis-config-generation \
    --verbose \
    /home/frappe/frappe-bench \
    && cd /home/frappe/frappe-bench \
    && bench get-app --branch=${REFRACTEC_BRANCH} ${REFRACTEC_REPO} \
    && bench get-app --branch=${DOPPIO_BRANCH} ${DOPPIO_REPO} \
    && echo "{}" > sites/common_site_config.json \
    && find apps -mindepth 1 -path "*/.git" | xargs rm -fr

# Build frontend assets
WORKDIR /home/frappe/frappe-bench
RUN bench build --app frappe && bench build --app refractec

# Build React frontend (supervisor mobile app)
WORKDIR /home/frappe/frappe-bench/apps/refractec/frontend
RUN npm ci && npm run build

# --------------- Stage 4: Production image ---------------
FROM base AS production

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

VOLUME [ \
    "/home/frappe/frappe-bench/sites", \
    "/home/frappe/frappe-bench/logs" \
]

CMD [ \
    "/home/frappe/frappe-bench/env/bin/gunicorn", \
    "--chdir=/home/frappe/frappe-bench/sites", \
    "--bind=0.0.0.0:8000", \
    "--threads=4", \
    "--workers=2", \
    "--worker-class=gthread", \
    "--worker-tmp-dir=/dev/shm", \
    "--timeout=120", \
    "--preload", \
    "frappe.app:application" \
]
