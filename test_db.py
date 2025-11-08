from azure.storage.blob import BlobServiceClient

# Your credentials from .env
account_name = "skillscreenstorage"
container_name = "audio-recordings"
sas_token ="sp=racwdl&st=2025-10-23T17:00:50Z&se=2026-01-01T02:15:50Z&spr=https&sv=2024-11-04&sr=c&sig=bHderF7bvEZSpwdIVzDveFNyNFQgBN6wuEuvHitfiiI%3D"  # Paste your actual token




try:
    # Create client
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=sas_token
    )
    
    # Try to list blobs
    container_client = blob_service_client.get_container_client(container_name)
    blobs = list(container_client.list_blobs())
    
    print("✅ Connection successful!")
    print(f"📦 Container: {container_name}")
    print(f"📁 Files found: {len(blobs)}")
    
    if blobs:
        for blob in blobs:
            print(f"  - {blob.name}")
    else:
        print("  (empty - no files yet)")
        
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")