# core/agent_registry.py

from core.bureau_pipeline import bureau_agent_pipeline
from core.credit_pipeline import credit_scoring_pipeline
from core.fraud_pipeline import fraud_detection_pipeline
from core.compliance_pipeline import compliance_agent_pipeline
from core.explainability_pipeline import explainability_agent_pipeline
AGENT_PIPELINES = {
    "bureau": bureau_agent_pipeline,
    "credit": credit_scoring_pipeline,
    "fraud": fraud_detection_pipeline,
    "compliance": compliance_agent_pipeline,
    "explainability": explainability_agent_pipeline,
}
