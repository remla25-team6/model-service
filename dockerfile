# Global args
ARG FLASK_PORT=8080
ARG FLASK_HOST=0.0.0.0
ARG BASE_URL="https://github.com/remla25-team6/model-training/releases/download/"

# Base stage
FROM python:3.12.10-slim AS base
# Redeclare ARGs
ARG FLASK_PORT
ARG FLASK_HOST
ARG BASE_URL
# Environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_PORT=${FLASK_PORT} \
    FLASK_HOST=${FLASK_HOST} \
    BASE_URL=${BASE_URL}
WORKDIR /app

# Build stage
FROM --platform=$BUILDPLATFORM base AS builder
# Disclaimer: Used ChatGPT o4-mini-high for instructions on how to install git.
# Install git and clean up apt cache
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*
# Install reqs for python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --user -r requirements.txt
# Fetch the NLTK stopwords corpus
RUN python -m nltk.downloader --quiet stopwords
# Copy flask webservice to app
COPY src/main/flask_service.py /app/

# Final runtime stage
FROM base
# Copy only the installed python packages and application code from the builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
# Ensure the user‑installed binaries are on PATH
ENV PATH=/root/.local/bin:${PATH}

ENTRYPOINT ["python", "flask_service.py"]