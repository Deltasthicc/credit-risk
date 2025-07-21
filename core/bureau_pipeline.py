import os
import re
import json
import requests
from sentence_transformers import SentenceTransformer
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from datetime import datetime

# Global configs
connection_string = "DefaultEndpointsProtocol=https;AccountName=bureausummariser2;AccountKey=NpVwVbISJiyycsABD8wOm86EscF/4gLv1ZxQoGVHu05clnCy9ImmhV1JPN5kuBbd9JxSaCL176pV+AStxnMA+A==;EndpointSuffix=core.windows.net"
container_name = "bureau-summariser-container"
AZURE_SEARCH_ENDPOINT = "https://bureau-agent.search.windows.net"
AZURE_SEARCH_KEY = "ChGGOA90c0DUSuFp3VQFqIuh2hUrTAODxez4oubIp6AzSeDcQrf8"
INDEX_NAME = "bureau-vector-index"
QUERY_TEXT = "What are the total assets and liabilities for the company?"

def extract_fields(text):
    fields = {
        "company_name": None,
        "industry": None,
        "annual_revenue": None,
        "employees": None,
        "years_in_business": None
    }
    key_metrics = {
        "revenue_growth": None,
        "profit_margin": None,
        "debt_to_equity": None
    }
    remaining = []

    lines = text.splitlines()

    for line in lines:
        clean_line = line.strip()
        lower = clean_line.lower()

        def extract_value(pattern, default_type=float):
            match = re.search(pattern, clean_line, re.IGNORECASE)
            if not match:
                return None
            try:
                return default_type(match.group(1).replace(",", ""))
            except:
                return None

        if "company name" in lower:
            parts = clean_line.split(":", 1)
            fields["company_name"] = parts[1].strip() if len(parts) > 1 else None

        elif "industry" in lower:
            parts = clean_line.split(":", 1)
            fields["industry"] = parts[1].strip() if len(parts) > 1 else None

        elif "annual revenue" in lower:
            fields["annual_revenue"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")

        elif "employees" in lower:
            fields["employees"] = extract_value(r"[:\s]\s*([\d,]+)", int)

        elif "years in business" in lower:
            fields["years_in_business"] = extract_value(r"[:\s]\s*([\d]+)", int)

        elif "revenue growth" in lower:
            key_metrics["revenue_growth"] = extract_value(r"[:\s]\s*([\d.]+)")

        elif "profit margin" in lower:
            key_metrics["profit_margin"] = extract_value(r"[:\s]\s*([\d.]+)")

        elif "debt to equity" in lower:
            key_metrics["debt_to_equity"] = extract_value(r"[:\s]\s*([\d.]+)")

        else:
            remaining.append(clean_line)

    return fields, key_metrics, " ".join(remaining)

import os
import re
import io
import json
import pandas as pd
from docx import Document
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from azure.storage.blob import BlobServiceClient

# === Blob Reader ===
def read_latest_blob_content():
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blobs = list(container_client.list_blobs())
    if not blobs:
        raise Exception("No documents found in blob container.")

    # Sort latest
    blobs.sort(key=lambda x: x.last_modified, reverse=True)
    latest_blob = blobs[0]
    blob_name = latest_blob.name.lower()
    print(f" Processing blob: {blob_name}")
    blob_data = container_client.download_blob(latest_blob.name).readall()

    if blob_name.endswith(".docx"):
        document = Document(io.BytesIO(blob_data))
        return "\n".join([para.text for para in document.paragraphs if para.text.strip()])
    elif blob_name.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(blob_data), engine="openpyxl")
        return df.to_string(index=False)
    else:
        raise Exception(f"Unsupported file type for '{blob_name}'")

# === Field Extractor ===
def extract_fields(text):
    fields = {
        "company_name": None,
        "industry": None,
        "annual_revenue": None,
        "employees": None,
        "years_in_business": None
    }
    key_metrics = {
        "revenue_growth": None,
        "profit_margin": None,
        "debt_to_equity": None
    }
    raw_values = {
        "revenue": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "equity": None
    }
    remaining = []

    for line in text.splitlines():
        clean_line = line.strip()
        lower = clean_line.lower()

        def extract_value(pattern, dtype=float):
            match = re.search(pattern, clean_line)
            if not match: return None
            try: return dtype(match.group(1).replace(",", ""))
            except: return None

        if "company name" in lower:
            parts = clean_line.split(":", 1)
            fields["company_name"] = parts[1].strip() if len(parts) > 1 else None
        elif "industry" in lower:
            parts = clean_line.split(":", 1)
            fields["industry"] = parts[1].strip() if len(parts) > 1 else None
        elif "annual revenue" in lower:
            fields["annual_revenue"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        elif "employees" in lower:
            fields["employees"] = extract_value(r"[:\s]\s*([\d,]+)", int)
        elif "years in business" in lower:
            fields["years_in_business"] = extract_value(r"[:\s]\s*([\d]+)", int)
        elif "revenue growth" in lower:
            key_metrics["revenue_growth"] = extract_value(r"[:\s]\s*([\d.]+)")
        elif "profit margin" in lower:
            key_metrics["profit_margin"] = extract_value(r"[:\s]\s*([\d.]+)")
        elif "debt to equity" in lower:
            key_metrics["debt_to_equity"] = extract_value(r"[:\s]\s*([\d.]+)")
        elif "revenue" in lower:
            raw_values["revenue"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        elif "net income" in lower:
            raw_values["net_income"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        elif "total assets" in lower:
            raw_values["total_assets"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        elif "total liabilities" in lower:
            raw_values["total_liabilities"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        elif "equity" in lower:
            raw_values["equity"] = extract_value(r"[:\s]\s*\$?([\d.,]+)")
        else:
            remaining.append(clean_line)

    # === Auto-compute missing metrics ===
    if key_metrics["debt_to_equity"] is None and raw_values["total_liabilities"] and raw_values["equity"]:
        try:
            key_metrics["debt_to_equity"] = round(raw_values["total_liabilities"] / raw_values["equity"], 2)
        except ZeroDivisionError:
            pass
    if key_metrics["profit_margin"] is None and raw_values["net_income"] and raw_values["revenue"]:
        try:
            key_metrics["profit_margin"] = round((raw_values["net_income"] / raw_values["revenue"]) * 100, 2)
        except ZeroDivisionError:
            pass

    return fields, key_metrics, "\n".join(remaining)

# === Main Bureau Agent Pipeline ===
def bureau_agent_pipeline():
    try:
        with open(os.path.join("output_data", "summary2.json"), "r", encoding="utf-8") as f:
            bureau_output = json.load(f)
    except Exception as e:
        return {
            "errorMessage": f"Could not load summary2.json: {e}",
            "status": "AgentStatus.failed"
        }

    # Extract fields from JSON
    try:
        fields = {
            "company_name": bureau_output.get("company_name"),
            "industry": bureau_output.get("industry"),
            "annual_revenue": bureau_output.get("annual_revenue"),
            "employees": bureau_output.get("employees"),
            "years_in_business": bureau_output.get("years_in_business")
        }

        key_metrics = bureau_output.get("key_financial_metrics", {})

        raw_summary = bureau_output.get("summary", "").strip()
        if not raw_summary:
            raw_summary = "No detailed financial summary available."

        return {
            "agentName": "Bureau Summariser",
            "agentDescription": "Analyzes and summarizes business documents and financial statements",
            "extractedData": {
                **fields,
                "key_financial_metrics": key_metrics
            },
            "summary": raw_summary,
            "completedAt": "2025-07-11T09:18:23.155598Z",
            "confidenceScore": 0.92,
            "status": "AgentStatus.complete",
            "errorMessage": None
        }

    except Exception as e:
        return {
            "errorMessage": f"Error parsing summary1.json content: {e}",
            "status": "AgentStatus.failed"
        }
# === CLI Debug/Test ===
if __name__ == "__main__":
    result = bureau_agent_pipeline()
    print(json.dumps(result, indent=2))
    print("\n Bureau Data Extraction Complete.")