import requests
import json
from sentence_transformers import SentenceTransformer

# --- Config ---
endpoint = "https://bureau-agent.search.windows.net"
index_name = "bureau-vector-index"
api_key = "ChGGOA90c0DUSuFp3VQFqIuh2hUrTAODxez4oubIp6AzSeDcQrf8"
query_text = "What are the total assets and liabilities for the company?"

# --- Generate vector embedding ---
model = SentenceTransformer("all-MiniLM-L6-v2")
query_vector = model.encode(query_text).tolist()

# --- Build the request ---
url = f"{endpoint}/indexes/{index_name}/docs/search?api-version=2023-07-01-preview"

headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

payload = {
    "search": query_text,
    "vector": {
        "value": query_vector,
        "fields": "content_vector",
        "k": 3
    },
    "top": 3
}

# --- Send the request ---
response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()
results = response.json()

# --- Display results ---
print("\n🔎 Top Results:\n")
for doc in results.get("value", []):
    print(f"Filename: {doc.get('filename')}")
    print(f"Score: {doc.get('@search.score'):.4f}")
    print(f"Snippet: {doc.get('content', '')[:300].strip()}...")
    print("-" * 60)