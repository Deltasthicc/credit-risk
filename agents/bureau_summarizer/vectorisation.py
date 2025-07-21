import os
import uuid
from sentence_transformers import SentenceTransformer
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SimpleField, SearchableField, SearchFieldDataType,
    VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration
)
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import VectorSearchProfile
from azure.storage.blob import BlobServiceClient

AZURE_SEARCH_ENDPOINT = "https://bureau-agent.search.windows.net"
AZURE_SEARCH_KEY = "ChGGOA90c0DUSuFp3VQFqIuh2hUrTAODxez4oubIp6AzSeDcQrf8"
INDEX_NAME = "bureau-vector-index"

BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=bureausummariser2;AccountKey=NpVwVbISJiyycsABD8wOm86EscF/4gLv1ZxQoGVHu05clnCy9ImmhV1JPN5kuBbd9JxSaCL176pV+AStxnMA+A==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "bureau-summariser-container"

DOWNLOAD_FOLDER = "output_data"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

model = SentenceTransformer("all-MiniLM-L6-v2")

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="filename", type=SearchFieldDataType.String),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=384,
        vector_search_profile_name="default"
    )
]

vector_search = VectorSearch(
    profiles=[
        VectorSearchProfile(name="default", algorithm_configuration_name="my-hnsw")
    ],
    algorithms=[
        HnswAlgorithmConfiguration(name="my-hnsw", kind="hnsw", parameters={"m": 4, "efConstruction": 400})
    ]
)

index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
print(f"Creating index: {INDEX_NAME} with fields: {fields}")

index_client = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=AzureKeyCredential(AZURE_SEARCH_KEY))


try:
    index_client.create_index(index)
    print(f" Created index: {INDEX_NAME}")
except Exception as e:
    print(f" Index creation failed: {e}")

blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

blobs = list(container_client.list_blobs())
documents = []

for blob in blobs:
    if blob.name.endswith('/'):
        continue

    download_path = os.path.join(DOWNLOAD_FOLDER, blob.name)
    with open(download_path, "wb") as f:
        stream = container_client.download_blob(blob.name)
        f.write(stream.readall())
    print(f" Downloaded: {download_path}")

    import docx2txt
    import pandas as pd

    if blob.name.endswith(".docx"):
        content = docx2txt.process(download_path)

    elif blob.name.endswith(".xlsx"):
        try:
            df = pd.read_excel(download_path, sheet_name=None)
            content = "\n".join([df[sheet].to_string() for sheet in df])
        except Exception as e:
            print(f"Error reading {blob.name}: {e}")
            content = ""

    else:
        with open(download_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()


    embedding = model.encode(content).tolist()

    documents.append({
        "id": str(uuid.uuid4()),
        "filename": blob.name,
        "content": content,
        "content_vector": embedding
    })

search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=AzureKeyCredential(AZURE_SEARCH_KEY))
result = search_client.upload_documents(documents)
print(f"Upload result: {result}")
for item in result:
    if not item.succeeded:
        print(f" Failed: {item.key} | Error: {item.error_message}")