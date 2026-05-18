# 🎨 Artflow

An automated **AI-powered product mockup pipeline** built with Flask. Upload an image, apply an AI style transform via OpenAI, render it onto a 3D cup using Blender, and receive the final result by email — all handled asynchronously.

## How It Works

```
Upload Image → OpenAI Style Transfer → Blender 3D Render → Email Delivery
```

## Stack

- **Flask** + Flask-RESTful + flask-smorest — REST API
- **OpenAI** — AI image transformation
- **Blender** — 3D rendering (runs as a Docker container)
- **Celery** + Redis — async task queue
- **PostgreSQL** — database
- **Docker Compose** — fully containerized environment

## Getting Started

```bash
git clone https://github.com/Mahdikhaloei/Artflow.git
cd Artflow
./project.py start -d
```

> Requires Docker & Docker Compose. Everything else (PostgreSQL, Redis, Blender, Celery worker) spins up automatically.

## CLI

```bash
./project.py start -d    # Start all services
./project.py stop        # Stop all services
./project.py shell       # Open app shell
./project.py mypy        # Run type checks
```

## Development

```bash
pip install pre-commit
pre-commit install && pre-commit install --hook-type pre-push
```

---

Built by [Mahdi Khaloei](https://github.com/Mahdikhaloei)
