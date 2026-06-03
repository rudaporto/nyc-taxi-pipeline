import pytest
from botocore.exceptions import ClientError

from api.db import get_pool, init_db
from api.main import MINIO_DATA_BUCKET_NAME
from api.s3 import get_minio_client


async def create_test_bucket(client, bucket_name: str):
    """Helper function to create a test bucket in MinIO."""
    try:
        await client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            raise


@pytest.fixture(scope="module")
async def minio_client():
    """Fixture to provide a MinIO client for tests."""
    client = await get_minio_client()
    yield client


@pytest.fixture(scope="module", autouse=True)
async def setup_minio(minio_client):
    """Setup MinIO client and ensure the bucket exists before running tests."""

    await create_test_bucket(minio_client, bucket_name=MINIO_DATA_BUCKET_NAME)

    yield  # Tests will run after this point


@pytest.fixture(scope="module", autouse=True)
async def init_db_fixture():
    """Fixture to initialize the database before running tests."""
    pool = await get_pool()
    await init_db(pool)
    yield  # Tests will run after this point
