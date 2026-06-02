import os
import tempfile
from pathlib import Path

import aiofiles
import pytest
from httpx import ASGITransport, AsyncClient

from api.config import MINIO_DATA_BUCKET_NAME
from api.main import app

CURRENT_YEAR = 2025
CHUNK_SIZE = 10 * 1024 * 1024
DATA_DIR = Path("data")


async def iter_file_chunks(path: str, chunk_size: int):
    async with aiofiles.open(path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk


@pytest.mark.anyio
@pytest.mark.parametrize(
    "year, month",
    [
        (2025, 1),
        (2025, 2),
        (2025, 3),
        (2025, 4),
        (2025, 5),
        (2025, 6),
        (2025, 7),
        (2025, 8),
        (2025, 9),
        (2025, 10),
        (2025, 11),
        (2025, 12),
    ],
)
async def test_ingest_data(year, month, minio_client):
    filename = f"yellow_tripdata_{year:04d}-{month:02d}.parquet"
    data_file = Path(DATA_DIR) / filename
    total_bytes = os.path.getsize(data_file)
    assert (
        total_bytes > 0
    ), f"Test data file {data_file} is empty, cannot perform ingestion test."

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            f"/ingest/{year}/{month}",
            content=iter_file_chunks(data_file, CHUNK_SIZE),
            headers={"Content-Type": "application/octet-stream"},
        )

    # check response status code and content
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}. Response content: {response.content}"
    assert (
        response.headers["Content-Type"] == "application/json"
    ), f"Expected Content-Type application/json, got {response.headers['Content-Type']}"
    assert (
        "message" in response.json()
    ), f"Expected 'message' key in response JSON, got {response.json()}"
    assert (
        response.json()["message"]
        == f"Data for {year}-{month:02d} ingested successfully. Total bytes: {total_bytes}."
    ), f"Expected message 'Data for {year}-{month:02d} ingested successfully. Total bytes: {total_bytes}.', got {response.json()['message']}"
    assert response.json() == {
        "message": f"Data for {year}-{month:02d} ingested successfully. Total bytes: {total_bytes}."
    }

    # download the ingested file from MinIO and verify its contents
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file_path = Path(tmp_file.name)
        await minio_client.download_fileobj(
            MINIO_DATA_BUCKET_NAME, f"yellow_tripdata_{year:04d}-{month:02d}.parquet", tmp_file
        )

        assert (
            tmp_file_path.exists()
        ), f"Expected file {tmp_file_path} to exist after ingestion."
        assert (
            os.path.getsize(tmp_file_path) == total_bytes
        ), f"Expected ingested file size to match original file size for {filename}."
