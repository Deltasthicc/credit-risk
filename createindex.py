import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType
)
from azure.search.documents import SearchClient
import uuid

endpoint = "https://bureausearchsvc.search.windows.net"
key = "U9XMLkaUoJ1z8AN7aMRAUMhYmNNLlyhNJTM1c1mof1AzSeCPowx9"
index_name = "bureau-index-final"

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True, retrievable=True, sortable=False, facetable=False, searchable=False),
    SimpleField(name="company_name", type=SearchFieldDataType.String, key=False, filterable=True, retrievable=True, sortable=True, facetable=False, searchable=True),
    SimpleField(name="cik", type=SearchFieldDataType.String, key=False, filterable=True, retrievable=True, sortable=True, facetable=False, searchable=False),
    SimpleField(name="fiscal_year", type=SearchFieldDataType.String, key=False, filterable=True, retrievable=True, sortable=True, facetable=False, searchable=False),
    SimpleField(name="revenue", type=SearchFieldDataType.Double, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="assets", type=SearchFieldDataType.Double, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="liabilities", type=SearchFieldDataType.Double, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="equity", type=SearchFieldDataType.Double, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="net_income", type=SearchFieldDataType.Double, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="country", type=SearchFieldDataType.String, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="industry", type=SearchFieldDataType.String, key=False, filterable=True, retrievable=True, sortable=True, facetable=True, searchable=False),
    SimpleField(name="report_url", type=SearchFieldDataType.String, key=False, filterable=False, retrievable=True, sortable=False, facetable=False, searchable=False),
    # Add the required searchable content field
    SimpleField(name="content", type=SearchFieldDataType.String, key=False, filterable=False, retrievable=True, sortable=False, facetable=False, searchable=True),
]

index = SearchIndex(name=index_name, fields=fields)

index_client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
try:
    index_client.create_index(index)
    print(f"Index '{index_name}' created successfully.")
except Exception as e:
    print(f"Index may already exist or error occurred: {e}")

# Load your data (list of dicts)
# Load list of records from JSON file
with open("normalized_financial_data (1).json", "r") as f:
    records = json.load(f)  # this is likely a list of dicts

documents = []
for record in records:
    documents.append({
        "id": str(uuid.uuid4()),
        "company_name": record.get("company_name", "Apple Inc."),
        "cik": record.get("cik", "0000320193"),
        "fiscal_year": record.get("fiscal_year", "2023"),
        "revenue": record.get("net_sales", 0),
        "assets": record.get("total_assets", 0),
        "liabilities": record.get("total_liabilities", 0),
        "equity": record.get("shareholders_equity", 0),
        "net_income": record.get("net_income", 0),
        "country": record.get("country", "United States"),
        "industry": record.get("industry", "Technology"),
        "report_url": record.get("report_url", "https://example.com/apple-q1-2023-report"),
        "content": record.get("content", "Full text or summary of the document here")
    })

# Upload to Azure Search
client = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))

# Upload document
result = client.upload_documents(documents=documents)
import pprint
pprint.pprint(documents[0]) 
print("Uploaded", len(documents), "documents:", result)