import os
from pathlib import Path

TMP_DATA_DIR = Path("/tmp")
CHUNK_SIZE = 8 * 1024 * 1024

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9020")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_DATA_BUCKET_NAME = os.getenv("MINIO_DATA_BUCKET_NAME", "data")
MINIO_KEY = os.getenv("MINIO_KEY", "my-key")
