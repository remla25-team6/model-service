FROM python:3.12.10-slim
ARG ML_MODEL_VERSION=v0.1.0
WORKDIR /app

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