# syntax=docker/dockerfile:1
# ATEMS Flask API — layered image for fast rebuilds.
#
# The previous `COPY . .` pulled every markdown note, local .db file, logs,
# and virtualenv into the build context (often >1 GB) and invalidated the
# app layer on every unrelated repo change. This version only copies the
# files the app actually imports at runtime, and pairs with .dockerignore
# to keep the build context slim.

# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# --- Dependency layer (changes only when requirements.txt changes) ----------
# pip cache is shared across all bot repos via BuildKit id=bots-pip
# (see /srv/dep-cache/README.md for purge tooling).
COPY requirements.txt .
RUN --mount=type=cache,id=bots-pip,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements.txt

# --- Application layer (changes on normal code commits) ---------------------
COPY atems.py /app/
COPY extensions.py /app/
COPY forms.py /app/
COPY routes.py /app/
COPY gunicorn.conf.py /app/
COPY models/ /app/models/
COPY utils/ /app/utils/
COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY migrations/ /app/migrations/

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "atems:app"]
