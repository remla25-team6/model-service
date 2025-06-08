FROM python:3.12.10-slim
ENV PYTHONUNBUFFERED=1

# Flask listening port
ARG FLASK_PORT=8080
ENV FLASK_PORT=${FLASK_PORT}
ARG FLASK_HOST=0.0.0.0
ENV FLASK_HOST=${FLASK_HOST}
# Model download URL (appended by {MODEL_VERSION})
ARG BASE_URL="https://github.com/remla25-team6/model-training/releases/download/"
ENV BASE_URL=${BASE_URL}

WORKDIR /app

# Disclaimer: Used ChatGPT o4-mini-high for instructions on how to install git.
# Install git and clean up apt cache
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*
# Install reqs for python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# Fetch the NLTK stopwords corpus
RUN python -m nltk.downloader --quiet stopwords
# Copy flask webservice to app
COPY src/main/flask_service.py /app/

ENTRYPOINT ["python", "flask_service.py"]