import os
summary_folder = os.path.join("output_data")
summary_files = [
    "BalanceSheetMicrosoft_xlsx_summary.txt",
    "CashFlowsMicrosoft_xlsx_summary.txt",
    "pnlMicrosoft_xlsx_summary.txt",
    "QualitativesMicrosoft_docx_summary.txt"
]
all_summaries = []
for fname in summary_files:
    path = os.path.join(summary_folder, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        all_summaries.append(f"--- Summary from {fname} ---\n{content}")
combined_input = "\n\n".join(all_summaries)
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://creditriskassessoragent-resource.services.ai.azure.com/api/projects/creditriskassessoragent"
)
meta_agent = project.agents.get_agent("asst_CybcvjGZj3NylmSR8sCWFCxq")  # Replace with your agent ID

meta_prompt = (
    "You are a financial meta-summarizer.\n"
    "You will receive multiple structured financial summaries, each from a different document for the same company.\n"
    "Your tasks:\n"
    "1. Integrate the information: Combine the key metrics and insights from all summaries into a single, unified summary. Identify trends, changes, or anomalies across the documents.\n"
    "2. Highlight important patterns: Note any significant increases, decreases, or unusual changes in financial metrics.\n"
    "3. Resolve inconsistencies: If there are conflicting or missing values, mention them clearly.\n"
    "4. Output: Present a single, structured summary as key-value pairs, followed by a concise narrative that highlights the overall financial health, risks, and noteworthy trends for the company.\n"
    "Do not simply concatenate the summaries. Instead, synthesize the information into a clear, insightful, and actionable summary suitable for further credit or fraud analysis.\n\n"
    + combined_input
)
#print("=== INPUT TO META AGENT ===")
#print(meta_prompt)
thread = project.agents.threads.create()
message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content=meta_prompt
)
run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=meta_agent.id
)
text_messages = project.agents.messages.list(
    thread_id=thread.id,
    order=ListSortOrder.ASCENDING
)

# After you get text_messages from the meta agent
meta_output = ""
for message in text_messages:
    if message.text_messages:
        candidate = message.text_messages[-1].text.value.strip()
        if candidate:
            meta_output = candidate  # Save the last non-empty response

if meta_output:
    # Save to file
    with open(os.path.join("output_data", "meta_narrative_summary.txt"), "w", encoding="utf-8") as f:
        f.write(meta_output)
    print("Meta narrative summary saved!\n")
else:
    print("No response from meta agent. Check your input and agent instructions.")

# --- Now, forward this to the credit scoring agent ---

# Read the saved summary
with open("C:/Users/Akshita/Desktop/project/output_data/meta_narrative_summary.txt", "r", encoding="utf-8") as f:
    summary_text = f.read()

# Send to credit scoring agent
credit_agent = project.agents.get_agent("asst_UwJI3hJ2Qi0nhN2a2DFodVNa")  # Replace with your agent ID

thread = project.agents.threads.create()
message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content=summary_text
)
run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=credit_agent.id
)
messages = project.agents.messages.list(
    thread_id=thread.id,
    order=ListSortOrder.ASCENDING
)

for message in messages:
    if message.text_messages:
        print("\n=== Credit Scoring Agent Response ===\n")
        print(message.text_messages[-1].text.value)