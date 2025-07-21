import os
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
)

LEGAL_NORMS = [
    "Does the document comply with KYC norms?",
    "Are there any signs of money laundering or suspicious activities?",
    "Is the content aligned with GDPR or Indian IT Act regulations?",
    "Have all required regulatory disclosures been properly made?",
    "Is there verifiable consent obtained from clients or stakeholders?",
    "Are there risks of legal liability or omission of critical terms?",
    "Does it violate financial or operational transparency norms?"
]

def compliance_agent_pipeline(summary_text: str) -> dict:
    agent = project.agents.get_agent("asst_jma5gWHJMxPQt271vldw4mwg")

    prompt = f"""
    You are a legal compliance checker agent. Given the following document summary, identify any violations or risks:

    Summary:
    {summary_text}

    Check the following:
    {chr(10).join(f"- {norm}" for norm in LEGAL_NORMS)}

    Respond in JSON format with keys: "compliance_issues", "risk_level", and "recommendations".
    """

    try:
        thread = project.agents.threads.create()
        project.agents.messages.create(thread_id=thread.id, role="user", content=prompt)
        project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

        # Get assistant's response
        messages = list(project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING))
        assistant_reply = next((m for m in reversed(messages) if m.role == "assistant"), None)

        if not assistant_reply:
            return {"error": "No response from agent."}

        content = assistant_reply.text_messages[0].text.value if assistant_reply.text_messages else ""

        # Remove code fences if present
        if content.startswith("```json"):
            content = content.strip("```json").strip("`").strip()

        return json.loads(content)

    except Exception as e:
        return {
            "error": "Unable to parse agent response.",
            "raw_output": content if 'content' in locals() else "",
            "details": str(e)
        }

# Example usage:
if __name__ == "__main__":
    summary_path = os.path.join("output_data", "rag_summary.txt")
    with open(summary_path, "r", encoding="utf-8") as f:
        raw_summary = f.read()

    compliance_result = compliance_agent_pipeline(raw_summary)
    print(json.dumps(compliance_result, indent=2, ensure_ascii=False))
