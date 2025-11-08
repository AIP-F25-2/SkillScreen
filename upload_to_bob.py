from azure.storage.blob import BlobServiceClient
import requests

# Your Azure credentials
account_name = "skillscreenstorage"
container_name = "audio-recordings"
sas_token ="sp=racwdl&st=2025-10-23T17:00:50Z&se=2026-01-01T02:15:50Z&spr=https&sv=2024-11-04&sr=c&sig=bHderF7bvEZSpwdIVzDveFNyNFQgBN6wuEuvHitfiiI%3D"  # Paste your actual SAS token

# Google Drive direct download URL
google_drive_url = "https://drive.google.com/uc?export=download&id=1cVGHWvrv2exkWg7bUQwEvwHQ6Xz4FwlN"
blob_name = "test-interview-q1.mp4"  # Name in Azure

try:
    # Step 1: Download from Google Drive
    print(f"📥 Downloading from Google Drive...")
    response = requests.get(google_drive_url, stream=True)
    response.raise_for_status()
    
    # Step 2: Upload to Azure Blob
    print(f"📤 Uploading to Azure Blob...")
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=sas_token
    )
    
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name
    )
    
    # Upload directly from response stream
    blob_client.upload_blob(response.content, overwrite=True)
    
    print(f"✅ Upload successful!")
    print(f"📍 Blob URL: https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}")
    print(f"📝 Use blob_name: {blob_name}")
    
except Exception as e:
    print(f"❌ Failed: {str(e)}")