from azure.storage.blob import BlobServiceClient
from io import StringIO
import pandas as pd
import os
def load_csv_from_blob() -> pd.DataFrame:
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("AZURE_STORAGE_CONTAINER")
    blob_name = os.getenv("AZURE_STORAGE_BLOB")
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service_client.get_container_client(container).get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return pd.read_csv(StringIO(data.decode("utf-8")))

