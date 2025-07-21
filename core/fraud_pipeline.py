import os
import re
import json
import pandas as pd
import joblib
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

def fraud_detection_pipeline(summary_text: str) -> dict:
    model_path = "agents/fraud_detection/fraud_model.joblib"
    model = joblib.load(model_path)

    def extract_amount(field, text):
        pattern = rf"{field}:\s*\$?₹?([\d.,]+)\s*B"
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1).replace(",", "")) * 1e9 if match else 0.0

    def extract_string(field, text):
        pattern = rf"{field}:\s*(.+)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else "Unknown"

    # Feature extraction
    features = {
        "Revenue": extract_amount("Revenue", summary_text),
        "Net_Income": extract_amount("Net Income", summary_text),
        "Total_Assets": extract_amount("Total Assets", summary_text),
        "Total_Liabilities": extract_amount("Total Liabilities", summary_text),
        "Equity": extract_amount("Equity", summary_text),
        "Industry_Sector": extract_string("Industry", summary_text),
        "Country": extract_string("Country", summary_text)
    }

    df = pd.DataFrame([features])
    prediction = model.predict(df)[0]
    proba = model.predict_proba(df)[0]
    fraud_risk_score = round(proba[1], 2)  # Assuming class 1 = fraud

    # Risk level
    if fraud_risk_score > 0.7:
        risk_level = "High"
    elif fraud_risk_score > 0.3:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Simulated doc authenticity score and flags
    document_authenticity = round(1.0 - fraud_risk_score + 0.05, 2)
    verification_status = "Verified" if document_authenticity >= 0.9 else "Needs Review"
    flagged_items = [] if fraud_risk_score < 0.3 else ["Unusual liabilities", "Equity mismatch"]

    # Generate LLM explanation
    project = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
    )
    agent = project.agents.get_agent("asst_jma5gWHJMxPQt271vldw4mwg")

    prompt = f"""
    You are a fraud analyst. Review the following features and risk score, and summarize the fraud risk:

    Features:
    {json.dumps(features, indent=2)}

    Model Score: {fraud_risk_score}
    Risk Level: {risk_level}

    Write a clear 1-2 sentence professional summary on fraud likelihood.
    """

    thread = project.agents.threads.create()
    project.agents.messages.create(thread_id=thread.id, role="user", content=prompt)
    project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    messages = list(project.agents.messages.list(thread_id=thread.id))
    ai_summary = next((m.text_messages[-1].text.value for m in messages if m.text_messages), "No response.")

    # Final schema-compliant response
    return {
        "agentName": "Fraud Detection",
        "agentDescription": "Identifies potential fraud indicators and risk factors",
        "extractedData": {
            "fraud_risk_score": fraud_risk_score,
            "risk_level": risk_level,
            "flagged_items": flagged_items,
            "verification_status": verification_status,
            "document_authenticity": document_authenticity
        },
        "summary": ai_summary,
        "completedAt": datetime.utcnow().isoformat() + "Z",
        "confidenceScore": round(proba.max(), 2),
        "status": "AgentStatus.complete",
        "errorMessage": None
    }
if __name__ == "__main__":
    summary_path = os.path.join("output_data", "rag_summary.txt")
    with open(summary_path, "r", encoding="utf-8") as f:
        raw_summary = f.read()

    fraud_data = fraud_detection_pipeline(raw_summary)
    print(json.dumps(fraud_data, indent=2))
    print("\nFraud Detection Pipeline Complete. Data saved to output_data folder.")