import joblib
import numpy as np
import json

def init():
    global model
    model_path = "credit_scoring_model.joblib"
    model = joblib.load(model_path)

def run(raw_data):
    data = json.loads(raw_data)
    features = [
        data["credit_util_ratio"],
        data["eps_basic"],
        data["eps_diluted"],
        data["avg_monthly_income"],
        data["cash_and_equivalents"],
        data["high_utilization_flag"]
    ]
    prediction = model.predict([features])
    return int(prediction[0])