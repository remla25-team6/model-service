FROM python:3.12.10-slim
ARG ML_MODEL_VERSION
ENV ML_MODEL_VERSION=${ML_MODEL_VERSION}

# Flask listening port
ARG FLASK_PORT=8080
ENV FLASK_PORT=${FLASK_PORT}
ARG FLASK_HOST=0.0.0.0
ENV FLASK_HOST=${FLASK_HOST}

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
# Copy model embeddings to webservice
COPY bow-${ML_MODEL_VERSION}.pkl /app/
COPY model-${ML_MODEL_VERSION}.pkl /app/

ENTRYPOINT ["python", "flask_service.py"]