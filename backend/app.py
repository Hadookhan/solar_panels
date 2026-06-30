from flask import Flask, request, jsonify
from flask_cors import CORS

import torch
import pandas as pd
import joblib

from model import SolarEnergyNN
from train import FEATURES


app = Flask(__name__)
CORS(app)


MODEL_PATH = "solar_model.pt"
SCALER_PATH = "solar_scaler.pkl"

model = SolarEnergyNN(input_size=len(FEATURES))
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

scaler = joblib.load(SCALER_PATH)

def predict_batch(candidates):
    df = pd.DataFrame(candidates)
    df = df[FEATURES]

    X = scaler.transform(df.values)
    X = torch.tensor(X, dtype=torch.float32)

    with torch.no_grad():
        preds = model(X).squeeze().numpy()

    return preds

def find_best_orientation(base_input):
    candidates = []

    for tilt in range(0, 91, 10):
        for azimuth in range(0, 360, 30):
            candidate = base_input.copy()
            candidate["panel_tilt"] = tilt
            candidate["panel_azimuth"] = azimuth
            candidates.append(candidate)

    predictions = predict_batch(candidates)

    best_index = predictions.argmax()
    best_candidate = candidates[best_index]

    return {
        "tilt": best_candidate["panel_tilt"],
        "azimuth": best_candidate["panel_azimuth"],
        "predicted_energy_kw": float(predictions[best_index])
    }

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Solar backend is running"
    })


@app.route("/api/predict-energy", methods=["POST"])
def predict_energy():
    data = request.json

    row = pd.DataFrame([data])
    row = row[FEATURES]

    X = scaler.transform(row.values)
    X = torch.tensor(X, dtype=torch.float32)

    with torch.no_grad():
        prediction = model(X).item()

    return jsonify({
        "predicted_energy_kw": prediction
    })


@app.route("/api/best-orientation", methods=["POST"])
def best_orientation():
    data = request.json

    best_result = {
        "tilt": None,
        "azimuth": None,
        "predicted_energy_kw": -1
    }

    for tilt in range(0, 91, 5):
        for azimuth in range(0, 360, 10):
            candidate = data.copy()
            candidate["panel_tilt"] = tilt
            candidate["panel_azimuth"] = azimuth

            row = pd.DataFrame([candidate])
            row = row[FEATURES]

            X = scaler.transform(row.values)
            X = torch.tensor(X, dtype=torch.float32)

            with torch.no_grad():
                predicted_energy = model(X).item()

            if predicted_energy > best_result["predicted_energy_kw"]:
                best_result = {
                    "tilt": tilt,
                    "azimuth": azimuth,
                    "predicted_energy_kw": predicted_energy
                }

    return jsonify(best_result)


@app.route("/api/best-house-orientation", methods=["POST"])
def best_house_orientation():
    data = request.json

    arrays = data["arrays"]
    weather = data["weather"]

    results = []

    for array in arrays:
        input_data = weather.copy()
        input_data["inverter_kw"] = data["inverter_kw"]
        input_data["installed_capacity_kwp"] = array["installed_capacity_kwp"]

        best = find_best_orientation(input_data)
        best["array_id"] = array["array_id"]

        results.append(best)

    return jsonify({
        "house_id": data.get("house_id"),
        "arrays": results
    })


if __name__ == "__main__":
    app.run(debug=True)