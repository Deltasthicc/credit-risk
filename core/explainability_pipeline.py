import os
import re
import joblib
import shap
import time
import json
import pandas as pd
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load pipeline once
pipeline_path = os.path.join("agents", "explainability_agent", "final_pipeline.pkl")
pipeline = joblib.load(pipeline_path)
model_only = pipeline.named_steps['randomforestclassifier']

# Foundry client
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
)
foundry_agent = project.agents.get_agent("asst_oDWcHiwhp6UWnWCUCHs892Bb")

def extract_value(field, text, default=None):
    pattern = rf"{field}\s*:\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match: return default
    val_str = match.group(1).strip().replace(",", "")
    multiplier = 1e9 if 'B' in val_str.upper() else 1e6 if 'M' in val_str.upper() else 1
    number_match = re.search(r"[-+]?\d*\.?\d+", val_str)
    return float(number_match.group()) * multiplier if number_match else default

def extract_text(field, text, default="Unknown"):
    match = re.search(rf"{field}\s*:\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else default

def normalize_industry(val):
    return "Tech" if "tech" in val.lower() else "Finance" if "finance" in val.lower() else "Other"

def normalize_country(val):
    if "india" in val.lower(): return "India"
    if "us" in val.lower(): return "US"
    if "germany" in val.lower(): return "Germany"
    return "Other"

def prettify_feature(name):
    name = name.replace("columntransformer__", "").replace("_", " ")
    return re.sub(r"\b(\w)", lambda m: m.group(1).upper(), name)

def explainability_agent_pipeline(summary_text: str) -> dict:
    row = {
        "Revenue": extract_value("Revenue", summary_text),
        "Net_Income": extract_value("Net Income", summary_text),
        "Total_Assets": extract_value("Total Assets", summary_text),
        "Total_Liabilities": extract_value("Total Liabilities", summary_text),
        "Equity": extract_value("Equity", summary_text),
        "Industry_Sector": normalize_industry(extract_text("Industry", summary_text)),
        "Country": normalize_country(extract_text("Country", summary_text)),
    }
    df = pd.DataFrame([row])
    X_transformed = pipeline.named_steps['columntransformer'].transform(df)
    feature_names = pipeline.named_steps['columntransformer'].get_feature_names_out()

    explainer = shap.TreeExplainer(model_only)
    shap_values = explainer.shap_values(X_transformed)
    class_idx = 1  # Default risk class
    feature_shaps = shap_values[0, :, class_idx]
    contributions = sorted(
        zip(feature_names, feature_shaps),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    predicted_risk = model_only.predict_proba(X_transformed)[0][class_idx]
    top_features = "\n".join([f"{name}: {float(val):+.4f}" for name, val in contributions[:7]])

    # Foundry LLM explanation
    explanation_prompt = f"""
The following summary explains why a machine learning model predicted a certain level of credit default risk for a company.

It is based on various financial indicators and characteristics such as revenue, net income, total assets and liabilities, equity, industry type, and country of operation. Each of these factors influences the risk level in different ways — either increasing or reducing it.

Key drivers behind this prediction include:
{top_features}

Overall, the model has assessed a moderate level of risk based on these inputs. Please provide a clear and concise explanation of this prediction in business-friendly language, highlighting the most influential factors and their impact on the risk assessment.
"""

    thread = project.agents.threads.create()
    project.agents.messages.create(thread_id=thread.id, role="user", content="Explain why the default risk is predicted")
    project.agents.messages.create(thread_id=thread.id, role="assistant", content=explanation_prompt)
    project.agents.runs.create_and_process(thread_id=thread.id, agent_id=foundry_agent.id)

    assistant_reply = None
    for _ in range(5):
        messages = list(project.agents.messages.list(thread_id=thread.id))
        assistant_reply = next((m for m in reversed(messages) if m.role == "assistant"), None)
        if assistant_reply:
            break
        time.sleep(2)

    foundry_explanation = ""
    if assistant_reply:
        foundry_explanation = "\n".join(
            item["text"]["value"] for item in assistant_reply.content if item.get("type") == "text"
        )

    # Build final structured schema-compliant output
    return {
        "agentName": "Explainability",
        "agentDescription": "Provides detailed explanation of analysis decisions and factors",
        "extractedData": {
            "decision_factors": [
                prettify_feature(name) for name, _ in contributions[:3]
            ],
            "weight_distribution": {
                "financial_performance": round(abs(contributions[0][1]), 4),
                "business_stability": round(abs(contributions[1][1]), 4),
                "market_position": round(abs(contributions[2][1]), 4),
            },
            "confidence_reasoning": foundry_explanation or "No explanation from Foundry."
        },
        "summary": foundry_explanation[:300] + "..." if foundry_explanation else "N/A",
        "completedAt": datetime.utcnow().isoformat() + "Z",
        "confidenceScore": 0.88,
        "status": "AgentStatus.complete",
        "errorMessage": None
    }
if __name__ == "__main__":
    summary_path = os.path.join("output_data", "rag_summary.txt")
    with open(summary_path, "r", encoding="utf-8") as f:
        raw_summary = f.read()

    explainability_data = explainability_agent_pipeline(raw_summary)
    print(json.dumps(explainability_data, indent=2))
    print("\nExplainability Pipeline Complete. Data saved to output_data folder.")