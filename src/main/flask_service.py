import os
import json
import typing as T
from pathlib import Path

from flask import Flask, request, jsonify
from flasgger import Swagger

#   Internal dependencies
# try: 
#     from lib_ml import preprocess 
# except ImportError as err:
#     raise RuntimeError("lib_ml package not found. Ensure it is installed in the image.") from err

#   Model loading helpers
def load_model(model_dir: str, model_file: str): # Probably going to download it from somewhere?
    """Load the trained model into memory (executed once at container start)."""
    full_path = Path(model_dir) / model_file
    if not full_path.exists():
        raise FileNotFoundError(f"Model artefact not found: {full_path.resolve()}")
    # Choose your preferred deserialization library (joblib, pickle, torch, tf…):
    import joblib
    return joblib.load(full_path)


#   Flask app
app = Flask(__name__)
swagger = Swagger(app)

# Load the model once at startup
# MODEL_DIR = os.getenv("MODEL_PATH", "./model")
# MODEL_FILE = os.getenv("MODEL_NAME", "model.pkl")
# MODEL = load_model(MODEL_DIR, MODEL_FILE)


#   Utility functions

def _predict_one(instance: dict) -> T.Any:
    """Preprocess a single JSON instance, run inference, and post-process."""
    # 1. Preprocess (expects `preprocess` to return model-ready features)
    features = preprocess(instance)           # type: ignore  (depends on your lib_ml)
    # 2. Model inference (sklearn-style `predict` assumed; adapt if needed)
    raw_pred = MODEL.predict([features])[0]   # type: ignore
    # 3. Postprocess if necessary (e.g. decoding class index to label)
    return raw_pred


#   Routes

# Health route for the future
# @app.route("/health", methods=["GET"])
# def health():
#     """Simple liveness probe for Kubernetes/Docker health-checks."""
#     return jsonify(status="ok", model_version=os.getenv("GIT_COMMIT", "dev")), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Submit some JSON data to be processed for prediction by ML model.
    Expects JSON payload: {"instances": [ {...}, {...} ]}
    where each `{...}` is a raw input instance consumable by your preprocessing fn.
    ---
    parameters:
      - name: input_data
        in: body
        description: JSON data to be processed for prediction by ML model
    responses:
      200:
        description: Outputs positive or negative dependent on data
    """
    payload = request.get_json(silent=True)
    if not payload or "instances" not in payload:
        return jsonify(error="Payload must be JSON with an 'instances' field"), 400

    instances = payload["instances"]
    try:
        preds = [_predict_one(inst) for inst in instances]
    except Exception as exc:  # broad catch to return graceful 5xx
        app.logger.exception("Prediction failed")
        return jsonify(error=str(exc)), 500

    return jsonify(predictions=preds), 200


# Main loop
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)