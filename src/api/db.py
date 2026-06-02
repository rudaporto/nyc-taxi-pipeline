from asyncpg import create_pool

from api.config import DB_URL
from api.jobs import JobNotFoundError, JobRequest, Status

create_schema_sql = """
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    file_key VARCHAR(500) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(
            dsn=DB_URL,
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_db(db_pool):
    """Initialize the database by creating necessary tables."""
    async with db_pool.acquire() as conn:
        await conn.execute(create_schema_sql)


async def add_job(db_pool, job: JobRequest):
    """Add a new job to the database."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO jobs (file_key, year, month, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            job.file_key,
            job.year,
            job.month,
            job.status.value,
            job.created_at,
            job.updated_at,
        )


async def get_next_pending_job(db_pool) -> JobRequest:
    """Get the next pending job from the database."""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, file_key, year, month, status, created_at, updated_at
                FROM jobs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """
            )

            if row:
                await conn.execute(
                    f"""
                    UPDATE jobs
                    SET status = '{Status.PROCESSING.value}', updated_at = NOW()
                    WHERE id = $1
                    """,
                    row["id"],
                )

                return JobRequest(
                    file_key=row["file_key"],
                    year=row["year"],
                    month=row["month"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

    raise JobNotFoundError("No pending jobs found.")
