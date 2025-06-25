# model-service

A lightweight Flask-based microservice for sentiment analysis, exposing a machine learning model via a REST API. This service is a component of the REMLA reference architecture and is intended to be queried by the `app-service` or any compatible HTTP client.

---

## Key Features

| Endpoint          | Description                                                                                                                    |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `POST /predict`   | Send raw review text and receives a predicted sentiment label ("pos" or "neg").                                              |
| `POST /correct`   | Submit feedback for a review to collect corrected labels for future model re-training.                           |
| Swagger UI        | A self-documenting API interface available at `http://<host>:<port>/apidocs`, allowing developers to interact with endpoints.       |
| Stateless Docker Image   | During the Docker build, the model and bag-of-words vectorizer are pulled from the appropriate model-training GitHub release based on version. |

---

## Repository Structure

```text
model-service/
├── .github/workflows/prerelease.yml # Release CI/CD pipeline
├── .github/workflows/release.yml    # Pre-release CI/CD pipeline
├── dockerfile                       # Docker image definition
├── requirements.txt                 # Python runtime dependencies
└── src/main/
    └── flask_service.py             # Flask application and API endpoints
````

Note: Model artifacts (`model-<version>.pkl`, `bow-<version>.pkl`) are not committed to the repository. They are dynamically downloaded during the image build based on the `ML_MODEL_VERSION`.

---

## Running Locally (Development)

### Prerequisites

* Python 3.10 or later
* pip
* The model files corresponding to your target version (`model-<version>.pkl`, `bow-<version>.pkl`) must be downloaded manually into the working directory.

### Steps

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Linux/macOS
venv\Scripts\activate         # On Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ML_MODEL_VERSION=v0.1.0                # or desired version
export FLASK_APP=src/main/flask_service.py

# Start the Flask server
flask run -p 8080
```

### Example Request

```bash
curl -X POST http://localhost:8080/predict \
     -H "Content-Type: application/json" \
     -d '{"input": "Loved it! Amazing food."}'
# Response: {"sentiment": "pos"}
```

---

## Running with Docker

### Build and Run

```bash
export ML_MODEL_VERSION=v0.1.0

docker build -t model-service:$ML_MODEL_VERSION .

docker run --rm -p 8080:8080 \
    -e ML_MODEL_VERSION=$ML_MODEL_VERSION \
    model-service:$ML_MODEL_VERSION
```

### Pull from GitHub Container Registry

```bash
docker pull ghcr.io/remla25-team6/model-service:latest
```

---

## API Reference

### `POST /predict`

Request:

```json
{ "input": "Terrible service, never again." }
```

Response:

```json
{ "sentiment": "neg" }
```

| Status Code | Description                             |
| ----------- | --------------------------------------- |
| 200         | Prediction successful                   |
| 400         | Missing / malformed request             |
| 500         | Server error through exception during preprocessing or inference |

---

### `POST /correct`

Request:

```json
{
  "entries": {
    "input": "Food was cold but staff were friendly.",
    "truth": "neg"
  }
}
```

Returns the same review, the user label, and the model label.

---

## CI/CD
This project uses GitHub Actions for automated container image releases.

### Release
To publish an official release:
1. Ensure all changes are committed and pushed to any desired `release` branch.
2. Tag the commit with a version like `v0.1.0` and push:
    ```bash
    git tag v0.1.0
    git push origin v0.1.0
    ```
3. This triggers the `release.yml` workflow, which:
   - Downloads the corresponding model artifacts (`model-<ver>.pkl`, `bow-<ver>.pkl`) from the `model-training` release.
   - Builds the Docker image with the specified model version.
   - Pushes the image to GitHub Container Registry (GHCR) with semantic tags:
     - `v0.1.0`, `0.1.latest`, `0.latest`, and `latest`.

### Pre-Release
To publish a pre-release:
1. Push a commit to the `main` branch (i.e. merge a pull request to `main`).
2. The `prerelease.yml` workflow automatically runs on every commit to `main`.
3. It builds the image and tags it using a timestamped version like `0.1.0-pre.20250625.123456`.
4. The images are available on GHCR for testing and staging environments.

---

## AI Disclaimer
Used ChatGPT-4o to refine this README and improve technical clarity.
