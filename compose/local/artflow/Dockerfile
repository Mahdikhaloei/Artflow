# Stage 1: Build Python wheels
FROM python:3.11-slim AS python

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential libpq-dev wget gnupg ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN addgroup --system flask && adduser --system --ingroup flask flask

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    fontconfig \
    docker.io \
    imagemagick \
    potrace \
    wget \
    xz-utils \
    libpq-dev \
    inkscape \
    xvfb \
    xauth \
    libx11-6 \
    libxrender1 \
    libgl1 \
    libglu1-mesa \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=python /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

COPY ./core/static/fonts/ /usr/share/fonts/truetype/custom/
RUN fc-cache -f -v

COPY --chown=flask:flask ./compose/local/artflow/start /start
RUN sed -i 's/\r$//g' /start && chmod +x /start

COPY --chown=flask:flask ./compose/local/artflow/celery/worker/start /start-celery-worker
RUN sed -i 's/\r$//g' /start-celery-worker && chmod +x /start-celery-worker

COPY --chown=flask:flask ./compose/local/artflow/boot.sh /boot.sh
RUN sed -i 's/\r$//g' /boot.sh && chmod +x /boot.sh

ENTRYPOINT ["/boot.sh"]
