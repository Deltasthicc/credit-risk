from flask import Flask, request, jsonify
from core.bureau_pipeline import bureau_agent_pipeline
from core.credit_pipeline import credit_scoring_pipeline
from core.fraud_pipeline import fraud_detection_pipeline
from core.compliance_pipeline import compliance_agent_pipeline
from core.explainability_pipeline import explainability_agent_pipeline
from core.smart_pipeline import run_smart_pipeline
import traceback
from core.blob_utils import upload_file_to_blob
from mcp.validator import validate_input_against_schema, validate_output_against_schema
import json
import os
from core.agent_registry import AGENT_PIPELINES

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "API is up and running!"

@app.route("/run-fraud", methods=["POST"])
def run_fraud():
    try:
        summary_text = open("output_data/rag_summary.txt", encoding="utf-8").read()
        fraud_result = fraud_detection_pipeline(summary_text)
        return jsonify(fraud_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run-compliance", methods=["POST"])
def run_compliance():
    try:
        summary_text = open("output_data/rag_summary.txt", encoding="utf-8").read()
        compliance_result = compliance_agent_pipeline(summary_text)
        return jsonify(compliance_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run-explainability", methods=["POST"])
def run_explainability():
    try:
        summary_text = open("output_data/rag_summary.txt", encoding="utf-8").read()
        explain_result = explainability_agent_pipeline(summary_text)
        return jsonify(explain_result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run-smart-controller", methods=["POST"])
def run_smart_controller():
    try:
        final_result = run_smart_pipeline()
        return jsonify(final_result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)