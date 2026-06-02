from pathlib import Path

import aiofiles
from fastapi import FastAPI, HTTPException, Path, Request

from .config import MINIO_DATA_BUCKET_NAME, TMP_DATA_DIR
from .data import validate_parquet_file
from .s3 import get_minio_client, put_file_to_minio

app = FastAPI()


@app.post("/ingest/{year}/{month}")
async def ingest_data(year: int, month: int, request: Request):
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid month: {month}. Month must be between 1 and 12.",
        )

    if year < 2015 or year > 2026:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid year: {year}. Year must be between 2015 and 2026.",
        )

    total_bytes = 0
    dest_path = TMP_DATA_DIR / f"yellow_tripdata_{year:04d}-{month:02d}.parquet"
    print(f"Starting ingestion for year: {year} and month: {month}...")

    content_type = request.headers.get("content-type", "")
    if "application/octet-stream" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be application/octet-stream.",
        )

    async with aiofiles.open(dest_path.absolute(), "wb") as f:
        async for chunk in request.stream():
            await f.write(chunk)
            total_bytes += len(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail=f"No data ingested for {year}-{month:02d}. The uploaded file was empty.",
        )

    try:
        validate_parquet_file(dest_path.absolute(), year, month)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    try:
        async with get_minio_client() as client:
            await put_file_to_minio(
                client,
                dest_path,
                bucket=MINIO_DATA_BUCKET_NAME,
                key=f"yellow_tripdata_{year:04d}-{month:02d}.parquet",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to MinIO: {e}",
        )
    finally:
        dest_path.unlink(missing_ok=True)

    return {
        "message": f"Data for {year}-{month:02d} ingested successfully. Total bytes: {total_bytes}."
    }
