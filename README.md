# 📦 model-service

A thin Flask micro-service that turns your trained machine-learning model into a production-ready REST API.

---

## ✨  Key features
| Feature | Description |
|---------|-------------|
| **ML `/predict` endpoint** | Send a list of JSON objects and receive predictions back in one call. |
| *Swagger UI** | Interactive docs are auto-generated at `http://HOST:PORT/apidocs`. |
| **CI/CD to GHCR** | A GitHub Actions workflow builds & pushes an image tagged with the Git ref (e.g. `v0.0.2`). |

---

# 🏁 Quick-start