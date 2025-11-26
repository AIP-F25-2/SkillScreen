"""
Azure Blob Storage service for resume uploads
"""
import os
import logging
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContentSettings
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class AzureResumeStorage:
    """Azure Blob Storage service for storing resumes"""
    
    def __init__(self):
        # Parse the SAS URL to get container URL and SAS token
        sas_url = os.getenv(
            "AZURE_RESUME_SAS_URL",
            "https://skillscreenstorage00.blob.core.windows.net/resumes?sp=racwdl&st=2025-11-18T22:03:40Z&se=2026-01-01T06:18:40Z&spr=https&sv=2024-11-04&sr=c&sig=OwDaTiu32nUCTpk3OCrcHtwbUELDWpGBh8PGcNZ3r0o%3D"
        )
        
        parsed_url = urlparse(sas_url)
        # Extract container name from path (e.g., "/resumes" -> "resumes")
        path_parts = [p for p in parsed_url.path.split('/') if p]
        self.container_name = path_parts[0] if path_parts else "resumes"
        self.account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.sas_token = parsed_url.query
        
        # Create blob service client with SAS token
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.sas_token
        )
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
    
    def upload_resume(self, file_content: bytes, candidate_id: str, filename: str) -> str:
        """
        Upload resume to Azure Blob Storage
        
        Args:
            file_content: File content as bytes
            candidate_id: Candidate ID (UUID string)
            filename: Original filename
            
        Returns:
            Full URL to the uploaded blob
        """
        try:
            # Create blob name: resumes/{candidate_id}/{filename}
            blob_name = f"resumes/{candidate_id}/{filename}"
            
            # Get blob client
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Determine content type
            content_type = "application/pdf"
            if filename.lower().endswith('.docx'):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.lower().endswith('.doc'):
                content_type = "application/msword"
            
            # Upload blob
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            
            # Return full URL
            blob_url = blob_client.url
            logger.info(f"Uploaded resume to Azure: {blob_name}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading resume to Azure: {str(e)}")
            raise
    
    def get_resume_url(self, candidate_id: str, filename: str) -> str:
        """Get the URL for a resume blob"""
        blob_name = f"resumes/{candidate_id}/{filename}"
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.url
    
    def delete_resume(self, candidate_id: str, filename: str) -> bool:
        """Delete a resume from Azure Blob Storage"""
        try:
            blob_name = f"resumes/{candidate_id}/{filename}"
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted resume from Azure: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting resume from Azure: {str(e)}")
            return False

