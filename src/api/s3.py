from pathlib import Path

import aioboto3

from api import config

_client = None


async def get_minio_client():
    global _client
    if _client is None:
        session = aioboto3.Session()
        _client = await session.client(
            "s3",
            endpoint_url=config.MINIO_ENDPOINT,
            # hardcoded region for MinIO, as it doesn't use real AWS regions
            region_name="us-east-1",
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
        ).__aenter__()
    return _client


async def close_minio_client():
    global _client
    if _client:
        await _client.__aexit__(None, None, None)
        _client = None


async def put_file_to_minio(client, file_path: Path, bucket: str, key: str):
    """Upload a file to MinIO from a local path."""
    with file_path.open("rb") as fin:
        await client.upload_fileobj(fin, bucket, key)


async def get_file_from_minio(client, bucket: str, key: str, dest_path: Path):
    """Download a file from MinIO to a local path."""
    with dest_path.open("wb") as fout:
        await client.download_fileobj(bucket, key, fout)
