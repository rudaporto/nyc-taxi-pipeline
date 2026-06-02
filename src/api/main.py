from contextlib import asynccontextmanager

import aiofiles
from fastapi import FastAPI, HTTPException, Request

from api.config import MINIO_DATA_BUCKET_NAME, TMP_DATA_DIR
from api.data import validate_parquet_file
from api.db import add_job, close_pool, get_next_pending_job, get_pool, init_db
from api.jobs import JobNotFoundError, JobRequest, now_utc
from api.s3 import close_minio_client, get_minio_client, put_file_to_minio

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()
    await init_db(pool)
    await get_minio_client()
    yield
    await close_minio_client()
    await close_pool()


app = FastAPI(lifespan=lifespan)


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
    file_key = f"yellow_tripdata_{year:04d}-{month:02d}.parquet"
    dest_path = TMP_DATA_DIR / file_key
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
        await put_file_to_minio(
            await get_minio_client(),
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

    now = now_utc()
    job = JobRequest(
        file_key=file_key,
        year=year,
        month=month,
        status="pending",
        created_at=now,
        updated_at=now,
    )

    db_pool = await get_pool()
    await add_job(db_pool, job)

    return {
        "message": f"Data for {year}-{month:02d} ingested successfully. Total bytes: {total_bytes}."
    }


@app.get("/jobs/next", response_model=JobRequest | None)
async def next_job():
    """Get the next pending job from the database."""
    pool = await get_pool()
    try:
        next = await get_next_pending_job(pool)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="No pending jobs found.")

    return next
