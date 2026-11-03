# Monitoring demo

Local read-only view of this Linux machine. The app listens on `127.0.0.1` only. Do not commit `.env`.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
cp .env.example .env
```

Set `SECRET_KEY` in `.env` to a long random string before starting.

## Run

```bash
python run.py
```

Open http://127.0.0.1:5000
