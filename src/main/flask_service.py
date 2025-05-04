import os
import typing as T
from pathlib import Path

from flask import Flask, jsonify, request
from flasgger import Swagger
from joblib import load
import pandas as pd

try:
    from lib_ml.preprocess import preprocess
except ImportError as err:
    raise RuntimeError("lib_ml package not found in the image.") from err

# Configurations (should be replaced with environment variables in future
MODEL_VERSION   = "v0.1.0"
MODEL_FILE      = Path(f"model-{MODEL_VERSION}.pkl")
MODEL_EMBEDDINGS = Path(f"bow-{MODEL_VERSION}.pkl")

# load artefacts once
def _load(path: Path, label: str):
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path.resolve()}")
    return load(path)

MODEL = _load(MODEL_FILE, "Model")           # ML model
CV_EMB = _load(MODEL_EMBEDDINGS, "Vectoriser")  # CountVectorizer word embeddings

# flask app
app     = Flask(__name__)
swagger = Swagger(app)

# helpers

# Converts the reviews payload to a pd DataFrame for model inference
def convert_to_df(string_review: str) -> pd.DataFrame:
    """
    Turn a string or list-of-strings into a DataFrame with column 'Review'.
    """
    if isinstance(string_review, str):
        return pd.DataFrame({"Review": [string_review]})
    else:
        raise ValueError("Invalid input format. Expected a string as input.")

# Predict sentiment for a single review
def _predict_one(review_text: str) -> int:
    """
    Convert string to DF -> preprocess → BoW vector embed → predict.  Works for ONE plain-string review.
    """
    df     = convert_to_df(review_text)
    corpus = preprocess(df, len(df))       # preprocess the review
    cleaned  = corpus[0]
    vec    = CV_EMB.transform([cleaned]).toarray()
    return int(MODEL.predict(vec)[0])

# routes
@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict sentiment for a single review.
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
            - input
          properties:
            input:
              type: string
              example: "Loved it! Some very good positive (or negative) review!"
    responses:
      200:
        description: Model prediction ("pos" = positive, "neg" = negative)
        schema:
          type: object
          properties:
            sentiment:
              type: string
              enum: ["pos", "neg"]
              example: "pos"
      400:
        description: Bad request – payload malformed
      500:
        description: Model inference failed on the server
    """
    payload = request.get_json(silent=True)
    if not payload or "input" not in payload:
        return jsonify(error="JSON body must contain an 'input' field"), 400

    try:
        pred = _predict_one(payload["input"])
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify(error=str(exc)), 500

    sentiment = "pos" if pred == 1 else "neg"
    return jsonify(sentiment=sentiment), 200

# Feedback sentiment for a single review
@app.route("/correct", methods=["POST"])
def correct():
    """
    Submit ground-truth feedback for a single prediction.
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
              type: object
              required:
                - input
                - truth
              properties:
                input:
                  type: string
                  example: "Loved it! Some very good positive review!"
                truth:
                  type: string
                  enum: ["pos", "neg"]
                  description: "User’s label: 'pos' = positive, 'neg' = negative"
    responses:
      200:
        description: Echoes user input, their label, and the model’s sentiment
        schema:
          type: object
          properties:
            input:
              type: string
            truth:
              type: string
              enum: ["pos", "neg"]
              example: "pos"
            prediction:
              type: string
              enum: ["pos", "neg"]
              example: "neg"
      400:
        description: Bad request – payload malformed
      500:
        description: Server error while processing feedback
    """
    payload = request.get_json(silent=True)
    if not payload or "entries" not in payload or not isinstance(payload["entries"], dict):
        return jsonify(error="JSON body must contain an 'entries' object"), 400

    entry = payload["entries"]
    if "input" not in entry or "truth" not in entry:
        return jsonify(error="'entries' must contain 'input' and 'truth'"), 400

    inp       = entry["input"]
    truth_raw = entry["truth"]
    if truth_raw not in {"pos", "neg"}:
        return jsonify(error="'truth' must be \"pos\" or \"neg\""), 400

    try:
        pred_int = _predict_one(inp)
    except Exception as exc:
        app.logger.exception("Correction handling failed")
        return jsonify(error=str(exc)), 500

    prediction = "pos" if pred_int == 1 else "neg"

    return jsonify(
        input=inp,
        truth=truth_raw,
        prediction=prediction
    ), 200

# main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
