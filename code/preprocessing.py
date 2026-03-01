# code/preprocessing.py
from pathlib import Path
import sys

import pandas as pd
import geopandas as gpd


CODE_DIR = Path(__file__).resolve().parent
REPO_DIR = CODE_DIR.parent
RAW_DIR = REPO_DIR / "data" / "raw-data"
DERIVED_DIR = REPO_DIR / "data" / "derived-data"

CRASH_PATH = RAW_DIR / "Traffic_Crashes_-_Crashes_20260224.csv"
OUT_PATH = DERIVED_DIR / "crashes_by_community_year_hour_type.csv"


from community_boundaries import community_boundaries


def load_crashes(crash_path: Path) -> pd.DataFrame:
    usecols = ["CRASH_DATE", "LATITUDE", "LONGITUDE", "FIRST_CRASH_TYPE"]
    df = pd.read_csv(crash_path, usecols=usecols, low_memory=False)

    df["CRASH_DATE"] = pd.to_datetime(
        df["CRASH_DATE"], errors="coerce", infer_datetime_format=True
    )

    df = df.dropna(subset=["CRASH_DATE", "LATITUDE", "LONGITUDE"]).copy()
    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()

    df["FIRST_CRASH_TYPE"] = (
        df["FIRST_CRASH_TYPE"].astype(str).str.strip().fillna("UNKNOWN")
    )

    df["year"] = df["CRASH_DATE"].dt.year
    df["hour"] = df["CRASH_DATE"].dt.hour
    return df


def main():
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    areas = community_boundaries()
    areas = areas[["COMMUNITY", "geometry"]]

    cr = load_crashes(CRASH_PATH)

    cr_gdf = gpd.GeoDataFrame(
        cr,
        geometry=gpd.points_from_xy(cr["LONGITUDE"], cr["LATITUDE"]),
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(cr_gdf, areas, how="inner", predicate="within")

    agg = (
        joined.groupby(["COMMUNITY", "year", "hour", "FIRST_CRASH_TYPE"])
        .size()
        .rename("crash_count")
        .reset_index()
    )

    agg.to_csv(OUT_PATH, index=False)

if __name__ == "__main__":
    main()