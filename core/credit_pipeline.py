import os
import re
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def credit_scoring_pipeline(summary: str) -> dict:
    project = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
    )
    agent = project.agents.get_agent("asst_OPFiIidA5lUgry5IBnze5eKd")

    prompt = f"""
    You are a credit scoring assistant. Based on the structured summary below, return:

    - Credit Score (AAA to DDD)
    - Probability of Default (PD Score) as a decimal (e.g., 0.04)
    - Risk Factors (bullet points or comma-separated list)
    - Financial Strength Score (0–1)
    - Market Position Score (0–1)
    - Summary for the rating

    Format strictly as JSON with keys:
    credit_score, probability_of_default, risk_factors, financial_strength_score, market_position_score, summary

    Summary:
    {summary}
    """

    thread = project.agents.threads.create()
    project.agents.messages.create(thread_id=thread.id, role="user", content=prompt)
    project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

    output = ""
    for msg in messages:
        if msg.role == "assistant" and msg.text_messages:
            output = msg.text_messages[-1].text.value
            break

    if output.startswith("```json"):
        output = output.strip("```json").strip("`").strip()

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        data = {}
        for line in output.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                k = key.strip().lower().replace(" ", "_")
                v = val.strip()
                if k == "risk_factors":
                    data[k] = [r.strip() for r in re.split(r",|-", v)]
                elif re.match(r"^\d+(\.\d+)?$", v):
                    data[k] = float(v)
                else:
                    data[k] = v

    return {
        "agentName": "Credit Score Rating",
        "agentDescription": "Calculates credit risk and assigns AAA–DDD rating",
        "extractedData": {
            "credit_score": data.get("credit_score", "Unknown"),
            "probability_of_default": safe_float(data.get("probability_of_default")),
            "risk_factors": data.get("risk_factors", []),
            "financial_strength_score": safe_float(data.get("financial_strength_score")),
            "market_position_score": safe_float(data.get("market_position_score"))
        },
        "summary": data.get("summary", ""),
        "completedAt": datetime.utcnow().isoformat() + "Z",
        "confidenceScore": 0.89,
        "status": "AgentStatus.complete",
        "errorMessage": None
    }