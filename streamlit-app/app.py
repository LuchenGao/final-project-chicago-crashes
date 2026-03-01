import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import streamlit as st
from pathlib import Path
from community_boundaries import community_boundaries

st.set_page_config(page_title="Chicago Crashes Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent  
RAW_DIR = BASE_DIR.parent / "data" / "raw-data"
DERIVED_DIR = BASE_DIR.parent / "data" / "derived-data"
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

# -------------------------
# Filter crashes
# -------------------------
df_filt = derived[
    (derived["year"] == year_selected) &
    (derived["hour"] == hour_selected) &
    (derived["FIRST_CRASH_TYPE"].isin(types_selected))
].copy()


crash_ct = (
    df_filt.groupby("COMMUNITY")["crash_count"]
    .sum()
    .reset_index()
)

areas_plot = boundaries_gdf.merge(crash_ct, on="COMMUNITY", how="left")
areas_plot["crash_count"] = areas_plot["crash_count"].fillna(0).astype(int)

# -------------------------
# Page
# -------------------------
st.title("Chicago Crashes Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Year", str(year_selected))
c2.metric("Hour", f"{hour_selected:02d}:00–{(hour_selected+1)%24:02d}:00")
c3.metric("Total crashes (filtered)", f"{int(areas_plot['crash_count'].sum()):,}")

fig, ax = plt.subplots(figsize=(9, 9))
areas_plot.plot(
    column="crash_count",
    cmap="OrRd",
    legend=True,
    ax=ax,
    edgecolor="white",
    linewidth=0.3
)
ax.set_axis_off()
ax.set_title(f"Crash Count by Community Area ({year_selected}, hour={hour_selected:02d})")

left, right = st.columns([2, 1])

with left:
    st.pyplot(fig, use_container_width=True)

with right:
    st.subheader("Top communities")
    top = (
        areas_plot[["COMMUNITY", "crash_count"]]
        .sort_values("crash_count", ascending=False)
        .head(15)
    )
    st.dataframe(top, use_container_width=True, height=520)