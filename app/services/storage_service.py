from __future__ import annotations
import boto3
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)

# Note: In production, use environment variables for these
# boto3 doesn't have native async, but we can wrap it or use aiobotocore 
# For now, sticking to spec: "boto3==1.34.0"

def get_s3_client():
    # If using Cloudflare R2, endpoint_url must be provided
    return boto3.client(
        's3',
        endpoint_url=settings.S3_PUBLIC_URL.replace("https://pub-", "https://"), # Example logic for R2 endpoint
        aws_access_key_id="YOUR_ACCESS_KEY",
        aws_secret_access_key="YOUR_SECRET_KEY",
        region_name="auto"
    )

async def upload_order_image(file: UploadFile, order_id: str) -> str:
    """Upload image, return public URL."""
    if not settings.S3_BUCKET_NAME:
         logger.warning("S3_BUCKET_NAME not configured. Mocking upload.")
         return f"https://mock-storage.com/orders/{order_id}/{file.filename}"

    file_ext = Path(file.filename).suffix
    key = f"orders/{order_id}/{uuid.uuid4()}{file_ext}"
    
    try:
        s3 = get_s3_client()
        # file.file is the underlying SpooledTemporaryFile
        s3.upload_fileobj(
            file.file,
            settings.S3_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": file.content_type}
        )
        return f"{settings.S3_PUBLIC_URL}/{key}"
    except Exception as e:
        logger.error(f"S3 Upload failed: {e}")
        raise
