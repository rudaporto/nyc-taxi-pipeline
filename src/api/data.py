import pandas as pd
import pyarrow.parquet as pq


def validate_parquet_file(dest_path: str, year: int, month: int):
    """Validate that the given file is a valid Parquet file."""
    try:
        table = pq.read_table(dest_path, columns=["tpep_pickup_datetime"])
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"Validation failed for {dest_path}: {e}")

    df = table.to_pandas()
    if "tpep_pickup_datetime" not in df.columns:
        dest_path.unlink(missing_ok=True)
        raise ValueError(
            f"Validation failed for {dest_path}: 'tpep_pickup_datetime' column is missing."
        )

    ts = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    month_mask = (ts.dt.year == year) & (ts.dt.month == month)
    if not month_mask.any():
        dest_path.unlink(missing_ok=True)
        raise ValueError(
            f"Validation failed for {dest_path}: No data for {year}-{month:02d}."
        )
