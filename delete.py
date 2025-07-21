from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient

endpoint = "https://bureausearchsvc.search.windows.net"
key = "U9XMLkaUoJ1z8AN7aMRAUMhYmNNLlyhNJTM1c1mof1AzSeCPowx9"
index_name = "bureau-index-v3"

index_client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
index_client.delete_index(index_name)
print(f"Deleted index: {index_name}")