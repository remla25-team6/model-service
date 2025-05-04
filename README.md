# 📦 model-service

A lightweight Flask micro‑service that exposes a **sentiment‑analysis model** through a REST API.  It belongs to the *model image* in the REMLA reference architecture and can be queried by the *app‑service* or any HTTP client.

---

## ✨  Key features

| Feature                    | Description                                                                                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`POST /predict`**        | Send raw review text → receive a sentiment label *("pos"/"neg")*.                                                                                              |
| **`POST /correct`**        | Submit feedback (ground‑truth sentiment) for a single review so new labels can be collected for future re‑training.                                            |
| **Swagger UI**             | Self‑documenting API at `http://HOST:PORT/apidocs`.  Try endpoints directly from the browser.                                                                  |
| **Stateless Docker image** | The pre‑trained model and its BoW vectoriser are pulled from the *model‑training* GitHub release during the Docker build, so the final image starts instantly. |
| **Automated GHCR release** | Pushing a Git tag (e.g. `v0.1.0`) triggers a workflow that builds & pushes an image with semantic tags (`:v0.1.0`, `:0.1.latest`, `:0.latest`, `:latest`).     |

---

## 🗂  Repository layout

```text
model-service/
├── .github/workflows/release.yml   # CI / CD pipeline
├── dockerfile                      # Image build recipe (downloads model artefacts)
├── requirements.txt                # Python run‑time deps
└── src/main/
    └── flask_service.py            # Application entry‑point (Flask + routes)
```

*The model artefacts (`model-<ver>.pkl`, `bow-<ver>.pkl`) are **not** stored in the repo; they are downloaded in the Docker build step from the `model-training` release that matches `ML_MODEL_VERSION`.*

---

## 🏁  Quick‑start (local dev)

> Requires Python ≥ 3.10 and `pip`.  You’ll also need the model artefacts in the working directory (download them from the corresponding GitHub release).

```bash
# 1  Install dependencies
pip install -r requirements.txt
python -m nltk.downloader stopwords  # one‑time corpus fetch

# 2  Download the artefacts (bash)
export VER=v0.1.0  # or whichever version you need
# via GitHub CLI (recommended)
GH_REPO=remla25-team6/model-training

gh release download "$VER" -R "$GH_REPO" \
  -p "model-${VER}.pkl" \
  -p "bow-${VER}.pkl" \
  -D src/main

# → files now live next to src/main/flask_service.py

# 3  Run the service
export FLASK_APP=src/main/flask_service.py
flask run -p 8080      # → http://localhost:8080
  Run the service
```

```bash
# Query the prediction endpoint
curl -X POST http://localhost:8080/predict \
     -H "Content-Type: application/json" \
     -d '{"input":"Loved it! Amazing food."}'
# → {"sentiment":"pos"}
```

---

## 🐳  Quick‑start (Docker)

```bash
# Build image using embedded artefact download
export ML_MODEL_VERSION=v0.1.0

docker build \
  --build-arg ML_MODEL_VERSION=$ML_MODEL_VERSION \
  -t model-service:$ML_MODEL_VERSION .

docker run --rm -p 8080:8080 model-service:$ML_MODEL_VERSION
```

## 🐳 Pull Docker image
```
docker pull ghcr.io/remla25-team6/model-service:latest
```

---

## 🛠  API reference

### `POST /predict`

```jsonc
// Request
{ "input": "Terrible service, never again." }

// Response 200
{ "sentiment": "neg" }
```

| Code | Meaning      | When                                         |
| ---- | ------------ | -------------------------------------------- |
| 200  | OK           | Valid request, prediction returned.          |
| 400  | Bad Request  | Missing / malformed `input`.                 |
| 500  | Server Error | Exception during preprocessing or inference. |

---

### `POST /correct`

```jsonc
{
  "entries": {
    "input": "Food was cold but staff were friendly.",
    "truth": "neg"
  }
}
```

Returns the same review, the user label, and the model label.

---

## ♻️  Release workflow (summary)

1. **Train & publish** a model in *model-training*; its release assets contain `model-<ver>.pkl` and `bow-<ver>.pkl`.
2. Tag `model-service` (`git tag v0.1.0 && git push origin v0.1.0`).
3. The workflow in `.github/workflows/release.yml` downloads the artefacts, builds the image, and pushes it to GHCR under multiple semantic tags.

The *app-service* pulls the appropriate tag (often `X.Y.latest`).

---


### AI DISCLAIMER
*This documentation has been generated with the help of ChatGPT o3.*
