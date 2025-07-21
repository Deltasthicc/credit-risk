import os
import re
import pandas as pd
import joblib
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

# === Load model ===
model = joblib.load("C:\\Users\\Akshita\\Desktop\\project\\agents\\fraud_detection\\fraud_model.joblib")

# === Read RAG summary ===
rag_summary_path = "C:\\Users\\Akshita\\Desktop\\project\\output_data\\rag_summary.txt"
if not os.path.exists(rag_summary_path):
    raise FileNotFoundError("RAG summary not found. Run bureau agent first.")

with open(rag_summary_path, "r", encoding="utf-8") as f:
    text = f.read()

# === Extract fields using regex ===
def extract_amount(field, text):
    pattern = rf"{field}:\s*\$?₹?([\d.,]+)\s*B"
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1).replace(",", "")) * 1e9 if match else 0.0

def extract_string(field, text):
    pattern = rf"{field}:\s*(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "Unknown"

# === Values from summary ===
revenue = extract_amount("Revenue", text)
net_income = extract_amount("Net Income", text)
total_assets = extract_amount("Total Assets", text)
liabilities = extract_amount("Total Liabilities", text)
equity = extract_amount("Equity", text)
country = extract_string("Country", text)
industry = extract_string("Industry", text)

# === Prepare input dataframe ===
input_df = pd.DataFrame([{
    "Revenue": revenue,
    "Net_Income": net_income,
    "Total_Assets": total_assets,
    "Total_Liabilities": liabilities,
    "Equity": equity,
    "Industry_Sector": industry,
    "Country": country
}])

# === Run prediction ===
prediction = model.predict(input_df)[0]
proba = model.predict_proba(input_df)[0]
result_text = (
    f" Fraud Detection Result\n"
    f"Prediction: {'Fraudulent' if prediction else 'Not Fraudulent'}\n"
    f"Confidence: {max(proba) * 100:.2f}%"
)

print("\n" + result_text)

# === Connect to Azure Agent ===
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://akshitasurya.services.ai.azure.com/api/projects/CreditRiskAssessor"
)

agent_id = "asst_jma5gWHJMxPQt271vldw4mwg"
agent = project.agents.get_agent(agent_id)
thread = project.agents.threads.create()

# === Push fraud result as message ===
project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Run fraud detection based on the extracted RAG summary."
)
project.agents.messages.create(
    thread_id=thread.id,
    role="assistant",
    content=rag_summary_path
)

# === Trigger the agent run ===
project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

# === Print response ===
messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for m in messages:
    if m.text_messages:
        print("\n Agent Response:\n" + m.text_messages[-1].text.value)
