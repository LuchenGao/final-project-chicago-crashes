import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

def community_boundaries(plot=False):
    base_dir = Path(__file__).resolve().parent
    repo_dir = base_dir.parent
    path = repo_dir / "data" / "raw-data" / "Boundaries_-_Community_Areas_20260122.csv"

    df = pd.read_csv(path)

    boundaries_gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["the_geom"]),
        crs="EPSG:4326"
    )

    if plot:
        fig, ax = plt.subplots(figsize=(8, 8))
        boundaries_gdf.plot(ax=ax, edgecolor="black", linewidth=0.6, facecolor="none")
        ax.set_axis_off()
        plt.show()

    return boundaries_gdf
