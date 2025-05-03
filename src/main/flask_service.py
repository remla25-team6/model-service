import os
import typing as T
from pathlib import Path

from flask import Flask, jsonify, request
from flasgger import Swagger
from joblib import load

try:
    from lib_ml import preprocess          
except ImportError as err:
    raise RuntimeError("lib_ml package not found in the image.") from err

# configurations
MODEL_VERSION   = "v0.1.0"
MODEL_FILE      = Path(f"model-{MODEL_VERSION}.pkl")
MODEL_EMBEDDINGS = Path(f"bow-{MODEL_VERSION}.pkl")

# load artefacts once
def _load(path: Path, label: str):
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.resolve()}")
    return load(path)

MODEL = _load(MODEL_FILE, "Model")           # ML model
EMB   = _load(MODEL_EMBEDDINGS, "Vectoriser")  # CountVectorizer

# flask app
app     = Flask(__name__)
swagger = Swagger(app)

# helpers
def _predict_one(review_text: str) -> int:
    """
    Clean → BoW → predict.  Works for ONE plain-string review.
    """
    cleaned = preprocess(review_text)[0] if isinstance(preprocess(review_text), list) else preprocess(review_text)
    vector  = EMB.transform([cleaned]).toarray()
    return int(MODEL.predict(vector)[0])

# routes
@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict sentiment for a batch of reviews.
    ---
    tags:
      - Inference
    consumes:
      - application/json
    parameters:
      - name: payload
        in: body
        required: true
        schema:
          type: object
          required:
            - reviews
          properties:
            reviews:
              type: array
              items:
                type: string
              example: ["Loved it!", "Terrible service"]
    responses:
      200:
        description: List of model predictions (1 = positive, 0 = negative)
        schema:
          type: object
          properties:
            predictions:
              type: array
              items:
                type: integer
              example: [1, 0]
      400:
        description: Bad request – payload malformed
      500:
        description: Model inference failed on the server
    """
    payload = request.get_json(silent=True)
    if not payload or "reviews" not in payload:
        return jsonify(error="JSON body must contain a 'reviews' array"), 400

    try:
        preds = [_predict_one(txt) for txt in payload["reviews"]]
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify(error=str(exc)), 500

    return jsonify(predictions=preds), 200


@app.route("/correct", methods=["POST"])
def correct():
    """
    Submit ground-truth feedback for earlier predictions.
    ---
    tags:
      - Feedback
    consumes:
      - application/json
    parameters:
      - name: payload
        in: body
        required: true
        schema:
          type: object
          required:
            - entries
          properties:
            entries:
              type: array
              items:
                type: object
                required:
                  - input
                  - truth
                properties:
                  input:
                    type: string
                    example: "Loved it!"
                  truth:
                    type: integer
                    enum: [0, 1]
                    description: 1 = positive, 0 = negative
    responses:
      200:
        description: Echoes model prediction, truth label and match flag
        schema:
          type: object
          properties:
            results:
              type: array
              items:
                type: object
                properties:
                  input:
                    type: string
                  prediction:
                    type: integer
                  truth:
                    type: integer
                  match:
                    type: boolean
      400:
        description: Bad request – payload malformed
      500:
        description: Server error while processing feedback
    """
    payload = request.get_json(silent=True)
    if not payload or "entries" not in payload:
        return jsonify(error="JSON body must contain an 'entries' array"), 400

    results: list[dict[str, T.Any]] = []
    try:
        for item in payload["entries"]:
            inp   = item["input"]
            truth = int(item["truth"])
            pred  = _predict_one(inp)
            results.append(
                {
                    "input": inp,
                    "prediction": pred,
                    "truth": truth,
                    "match": pred == truth,
                }
            )
            # TODO: persist (inp, truth, pred) for future re-training
    except Exception as exc:
        app.logger.exception("Correction handling failed")
        return jsonify(error=str(exc)), 500

    return jsonify(results=results), 200


# main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
