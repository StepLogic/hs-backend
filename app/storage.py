import os
import boto3
from botocore.config import Config

_S3 = None


def _client():
    global _S3
    if _S3 is None:
        _S3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            config=Config(signature_version="s3v4"),
        )
    return _S3


def generate_upload_url(key: str, content_type: str, expiry: int = 300) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": os.getenv("S3_BUCKET"), "Key": key, "ContentType": content_type},
        ExpiresIn=expiry,
    )


def generate_download_url(key: str, expiry: int = 3600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": os.getenv("S3_BUCKET"), "Key": key},
        ExpiresIn=expiry,
    )
