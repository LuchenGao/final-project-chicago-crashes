import pandas as pd
from matplotlib import cm, colors
import geopandas as gpd
import streamlit as st
from pathlib import Path
import pydeck as pdk
import json
import numpy as np
from community_boundaries import community_boundaries

st.set_page_config(page_title="Chicago Crashes Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent  
RAW_DIR = BASE_DIR.parent / "data" / "raw-data"
DERIVED_DIR = BASE_DIR.parent / "data" / "derived-data"
SPEED_CAM_PATH = RAW_DIR / "Speed_Camera_Locations_20260222.csv"
REDLIGHT_CAM_PATH = RAW_DIR / "Red_Light_Camera_Locations_20260122.csv"
DERIVED_PATH = DERIVED_DIR / "crashes_by_community_year_hour_type.csv"

@st.cache_data(show_spinner=False)
def get_boundaries():
    return community_boundaries()

@st.cache_data(show_spinner=False)
def load_derived(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["FIRST_CRASH_TYPE"] = df["FIRST_CRASH_TYPE"].astype(str).str.strip().fillna("UNKNOWN")

    df["crash_count"] = pd.to_numeric(df["crash_count"], errors="coerce").fillna(0).astype(int)
    df["fatal_crashes"] = pd.to_numeric(df["fatal_crashes"], errors="coerce").fillna(0).astype(int)

    return df

@st.cache_data(show_spinner=False)
def load_speed_cameras(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.astype(str).str.strip()

    df["GO-LIVE DATE"] = pd.to_datetime(df["GO-LIVE DATE"], errors="coerce")
    df["go_live_year"] = df["GO-LIVE DATE"].dt.year

    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")

    df = df.dropna(subset=["LATITUDE", "LONGITUDE", "go_live_year"]).copy()
    return df



@st.cache_data(show_spinner=False)
def load_redlight_cameras(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.astype(str).str.strip()

    df["GO LIVE DATE"] = pd.to_datetime(df["GO LIVE DATE"], errors="coerce")
    df["go_live_year"] = df["GO LIVE DATE"].dt.year

    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")

    df = df.dropna(subset=["LATITUDE", "LONGITUDE", "go_live_year"]).copy()
    return df


# -------------------------
# Load data
# -------------------------
boundaries_gdf = get_boundaries()
derived = load_derived(DERIVED_PATH)

# -------------------------
# Sidebar filters
# -------------------------
st.sidebar.header("Filters")

years = sorted(derived["year"].dropna().unique().tolist())
year_selected = st.sidebar.selectbox("Year", options=years, index=len(years) - 1)

hour_selected = st.sidebar.slider("Hour of day (0–23)", min_value=0, max_value=23, value=0, step=1)

all_types = sorted(derived["FIRST_CRASH_TYPE"].dropna().unique().tolist())
types_selected = st.sidebar.multiselect(
    "Crash types (FIRST_CRASH_TYPE)",
    options=all_types,
    default=all_types
)

camera_selected = st.sidebar.multiselect(
    "Show cameras (go-live strictly before selected year)",
    options=["Speed cameras", "Red light cameras"],
    default=[]
)

# -------------------------
# Filter crashes
# -------------------------
df_filt = derived[
    (derived["year"] == year_selected) &
    (derived["hour"] == hour_selected) &
    (derived["FIRST_CRASH_TYPE"].isin(types_selected))
].copy()


crash_ct = (
    df_filt.groupby("COMMUNITY")[["crash_count", "fatal_crashes"]]
    .sum()
    .reset_index()
)

areas_plot = boundaries_gdf.merge(crash_ct, on="COMMUNITY", how="left")
areas_plot["crash_count"] = areas_plot["crash_count"].fillna(0).astype(int)
areas_plot["fatal_crashes"] = areas_plot["fatal_crashes"].fillna(0).astype(int)

areas_plot["fatal_rate"] = np.where(
    areas_plot["crash_count"] > 0,
    areas_plot["fatal_crashes"] / areas_plot["crash_count"],
    np.nan
)
areas_plot["fatal_rate_pct"] = (areas_plot["fatal_rate"] * 100).round(2)

# -------------------------
# Page
# -------------------------
st.title("Chicago Crashes Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Year", str(year_selected))
c2.metric("Hour", f"{hour_selected:02d}:00–{(hour_selected+1)%24:02d}:00")
c3.metric("Total crashes (filtered)", f"{int(areas_plot['crash_count'].sum()):,}")

show_speed = "Speed cameras" in camera_selected
show_red = "Red light cameras" in camera_selected

speed_df = None
red_df = None

if show_speed:
    speed_df = load_speed_cameras(SPEED_CAM_PATH)
    speed_df = speed_df[speed_df["go_live_year"] < year_selected].copy()

if show_red:
    red_df = load_redlight_cameras(REDLIGHT_CAM_PATH)
    red_df = red_df[red_df["go_live_year"] < year_selected].copy()

# -------------------------
# Camera counts per COMMUNITY (for tooltip)
# -------------------------
areas_plot["speed_cam_count"] = 0
areas_plot["red_cam_count"] = 0

# Speed cameras -> count per community
if show_speed and speed_df is not None and len(speed_df) > 0:
    sp_gdf = gpd.GeoDataFrame(
        speed_df,
        geometry=gpd.points_from_xy(speed_df["LONGITUDE"], speed_df["LATITUDE"]),
        crs="EPSG:4326",
    )
    sp_join = gpd.sjoin(
        sp_gdf,
        boundaries_gdf[["COMMUNITY", "geometry"]],
        how="inner",
        predicate="within",
    )
    if len(sp_join) > 0:
        sp_ct = sp_join.groupby("COMMUNITY").size()
        # 用 map 回填（不会出现 _x/_y）
        areas_plot["speed_cam_count"] = (
            areas_plot["COMMUNITY"].map(sp_ct).fillna(0).astype(int)
        )

# Red light cameras -> count per community
if show_red and red_df is not None and len(red_df) > 0:
    rl_gdf = gpd.GeoDataFrame(
        red_df,
        geometry=gpd.points_from_xy(red_df["LONGITUDE"], red_df["LATITUDE"]),
        crs="EPSG:4326",
    )
    rl_join = gpd.sjoin(
        rl_gdf,
        boundaries_gdf[["COMMUNITY", "geometry"]],
        how="inner",
        predicate="within",
    )
    if len(rl_join) > 0:
        rl_ct = rl_join.groupby("COMMUNITY").size()
        areas_plot["red_cam_count"] = (
            areas_plot["COMMUNITY"].map(rl_ct).fillna(0).astype(int)
        )

areas_plot["camera_total"] = areas_plot["speed_cam_count"] + areas_plot["red_cam_count"]
areas_plot["crash_per_camera"] = np.where(
    areas_plot["camera_total"] > 0,
    (areas_plot["crash_count"] / areas_plot["camera_total"]).round(1),
    np.nan,
)

# -------------------------
# Interactive map (pydeck) + table (same layout)
# -------------------------

COLOR_SCHEME = "OrRd"

vals = areas_plot["crash_count"].fillna(0).astype(float).values
vmax = vals.max() if len(vals) else 0.0

if vmax <= 0:
    areas_plot["fill"] = [[220, 220, 220, 140]] * len(areas_plot)
else:
    norm = colors.Normalize(vmin=0, vmax=vmax)
    cmap = cm.get_cmap(COLOR_SCHEME)

    fills = []
    for v in vals:
        r, g, b, a = cmap(norm(v))  # 0-1 float
        fills.append([int(255*r), int(255*g), int(255*b), 160])  # alpha 160
    areas_plot["fill"] = fills

geojson = json.loads(areas_plot.to_json())

community_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color="properties.fill",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
)

layers = [community_layer]

if show_speed and speed_df is not None and len(speed_df) > 0:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=speed_df,
            get_position="[LONGITUDE, LATITUDE]",
            get_radius=40,
            radius_min_pixels=2,
            radius_max_pixels=6,
            get_fill_color=[0, 90, 255, 180],  # blue
            pickable=False,
        )
    )

if show_red and red_df is not None and len(red_df) > 0:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=red_df,
            get_position="[LONGITUDE, LATITUDE]",
            get_radius=40,
            radius_min_pixels=2,
            radius_max_pixels=6,
            get_fill_color=[0, 160, 0, 180],   # green
            pickable=False,
        )
    )

tooltip = {
    "html": f"""
    <b>Community:</b> {{COMMUNITY}}<br/>
    <b>Total crashes:</b> {{crash_count}}<br/>
    <b>Fatal crashes:</b> {{fatal_crashes}}<br/>
    <b>Fatal rate:</b> {{fatal_rate_pct}}%<br/>
    <b>Speed cameras:</b> {{speed_cam_count}}<br/>
    <b>Red light cameras:</b> {{red_cam_count}}<br/>
    <b>Crashes per camera:</b> {{crash_per_camera}}
    """,
    "style": {"backgroundColor": "white", "color": "black"},
}

center = boundaries_gdf.geometry.unary_union.centroid
view_state = pdk.ViewState(latitude=center.y, longitude=center.x, zoom=10.3)

deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
)

left, right = st.columns([2, 1])

with left:
    st.subheader(f"Crash Count by Community ({year_selected}, hour={hour_selected:02d})")
    st.pydeck_chart(deck, use_container_width=True)

with right:
    st.subheader("Top communities")
    top = (
        areas_plot[["COMMUNITY", "crash_count"]]
        .sort_values("crash_count", ascending=False)
        .head(15)
    )
    st.dataframe(top, use_container_width=True, height=520)