from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict


class JobNotFoundError(Exception):
    """Custom exception for when a job is not found in the database."""

    pass


def now_utc():
    return datetime.now(timezone.utc)


class Status(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRequest(BaseModel):
    file_key: str
    year: int
    month: int
    status: Status
    created_at: datetime | None
    updated_at: datetime | None

    # add example for documentation
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_key": "path/yellow_tripdata_2025-01.parquet",
                "year": 2025,
                "month": 1,
                "status": "pending",
                "created_at": now_utc(),
                "updated_at": now_utc(),
            }
        }
    )
