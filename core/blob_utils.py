from azure.storage.blob import BlobServiceClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=ragsummary;AccountKey=Tq0ASCNFfDiRsomF1g5caLsDVmq0+MSA0XwJCiUANpvDz9htutMCrAF+2bUOtva17eURK8x8sf1X+AStQFlI4A==;EndpointSuffix=core.windows.net"
container_name = "rag-summary"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

def upload_file_to_blob(file_obj, blob_name: str):
    """
    Uploads a file-like object (e.g., Flask FileStorage) to Azure Blob Storage.
    """
    container_client.upload_blob(name=blob_name, data=file_obj.stream, overwrite=True)
    return f"Uploaded to blob: {blob_name}"
