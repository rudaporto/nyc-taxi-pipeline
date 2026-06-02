import argparse
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

DATA_DIR = "data"
DATA_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def build_url(year: int, month: int) -> str:
    """Build the URL for the given year and month."""
    return f"{DATA_BASE_URL}/yellow_tripdata_{year:04d}-{month:02d}.parquet"


async def download_data(session: aiohttp.ClientSession, year: int, month: int):
    url = build_url(year, month)
    logger.info(f"Downloading data from {url}...")
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.read()
            filename = f"{DATA_DIR}/yellow_tripdata_{year:04d}-{month:02d}.parquet"
            with open(filename, "wb") as f:
                f.write(data)
            logger.info(f"Data downloaded and saved to {filename}.")
        else:
            logger.error(
                f"Failed to download data. HTTP status code: {response.status}"
            )


async def download_all_data(year: int, months: list[int]):
    async with aiohttp.ClientSession() as session:
        tasks = [download_data(session, year, month) for month in months]
        await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(
        description="Download NYC taxi data for a given year and month."
    )
    parser.add_argument("year", type=int, help="The year to download data for.")
    parser.add_argument(
        "month",
        type=int,
        help="The month to download data for (0 for all months).",
        nargs="?",
        default=0,
    )
    args = parser.parse_args()

    months = list(range(1, 13)) if args.month == 0 else [args.month]
    asyncio.run(download_all_data(args.year, months))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
