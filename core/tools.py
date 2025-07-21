# core/tools.py

from core.credit_pipeline import credit_scoring_pipeline
from core.fraud_pipeline import fraud_detection_pipeline
from core.explainability_pipeline import explainability_agent_pipeline
from core.compliance_pipeline import compliance_agent_pipeline

def run_credit_tool(summary_text: str) -> dict:
    return credit_scoring_pipeline(summary_text)

def run_fraud_tool(summary_text: str) -> dict:
    return fraud_detection_pipeline(summary_text)

def run_explainability_tool(summary_text: str) -> dict:
    return explainability_agent_pipeline(summary_text)

def run_compliance_tool(summary_text: str) -> dict:
    return compliance_agent_pipeline(summary_text)