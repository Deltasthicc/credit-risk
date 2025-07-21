import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from core.bureau_pipeline import bureau_agent_pipeline
from core.tools import (
    run_credit_tool,
    run_fraud_tool,
    run_explainability_tool,
    run_compliance_tool
)

output_template = {
    "bureau_summary": None,
    "credit_scoring": None,
    "fraud_detection": None,
    "explainability": None,
    "compliance_check": None
}

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
)

agent = project.agents.get_agent("asst_yv7fmqGQwS0xSBs4uE7D6zIO")  

def run_smart_pipeline():
    result = output_template.copy()

    # Step 1: Bureau Agent — DO NOT load JSON manually!
    bureau_output = bureau_agent_pipeline()  # This handles blob + agent
    if bureau_output.get("status") != "AgentStatus.complete":
        raise RuntimeError(f"Bureau agent failed: {bureau_output.get('errorMessage')}")

    summary = bureau_output.get("summary", "").strip()
    if not summary:
        summary = "No detailed financial summary available."

    result["bureau_summary"] = bureau_output

    # Step 2: Controller Agent — Decide which tools to run
    thread = project.agents.threads.create()

    project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content="Analyze this financial summary and suggest which tools to use:"
    )
    project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=summary
    )

    toolset_description = [
        "credit scoring",
        "fraud detection",
        "explainability",
        "compliance"
    ]

    instructions = f"""
You are an AI controller agent. Your job is to read the financial summary and decide which tools to invoke from the toolset below:

Toolset: {toolset_description}

Respond ONLY with a JSON list of tool names to run. Use exact names like:
- "credit scoring"
- "fraud detection"
- "explainability"
- "compliance"

Do NOT include explanations, markdown, or text outside the JSON list.
Only respond with: ["credit scoring", "fraud detection"] or similar.
"""

    project.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id,
        instructions=instructions
    )

    # Step 3: Parse assistant reply
    messages = list(project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING))
    tools_response = next((m.text_messages[-1].text.value for m in messages if m.role == "assistant"), "[]")

    try:
        tools_to_run = json.loads(tools_response)
    except Exception:
        raise ValueError(f"Agent returned invalid JSON: {tools_response}")

    # Step 4: Run tools
    result["credit_scoring"] = run_credit_tool(summary)
    result["explainability"] = run_explainability_tool(summary)

    if "fraud detection" in tools_to_run:
        result["fraud_detection"] = run_fraud_tool(summary)
    if "compliance" in tools_to_run:
        result["compliance_check"] = run_compliance_tool(summary)

    return result