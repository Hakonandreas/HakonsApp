import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta

from functions.elhub_utils import load_elhub_data, load_elhub_consumption

st.set_page_config(layout="wide")
st.title("Energy Map – Norway Price Areas (NO1–NO5)")

# ------------------------------------------------------------------------------
# Load GeoJSON
# ------------------------------------------------------------------------------
geojson_path = Path(__file__).parent / "data" / "ElSpot_omraade.geojson"
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# ------------------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------------------
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None

if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

if "area_means" not in st.session_state:
    st.session_state.area_means = None

# ------------------------------------------------------------------------------
# UI – choose Production / Consumption
# ------------------------------------------------------------------------------
data_type = st.radio("Select data type:", ["Production", "Consumption"], horizontal=True)

# Load correct dataset and apply correct group column
if data_type == "Production":
    df = load_elhub_data()
    group_col = "productiongroup"
else:
    df = load_elhub_consumption()
    group_col = "consumptionsgroup"

# Group selector
groups = sorted(df[group_col].dropna().unique().tolist())
group = st.selectbox("Select group:", groups)

# Time window
days = st.slider("Time interval (days):", 1, 30, 7)

# ------------------------------------------------------------------------------
# Prepare filtered dataframe
# ------------------------------------------------------------------------------
df = df.copy()
df["starttime"] = pd.to_datetime(df["starttime"])

end_time = df["starttime"].max()
start_time = end_time - timedelta(days=days)

df_period = df[
    (df["starttime"] >= start_time) &
    (df["starttime"] <= end_time) &
    (df[group_col] == group)
]

# ------------------------------------------------------------------------------
# Compute mean per price area (NO1–NO5)
# ------------------------------------------------------------------------------
# Use pricearea + quantitykwh (NEW!)
means = (
    df_period.groupby("pricearea")["quantitykwh"]
    .mean()
    .to_dict()
)

# Ensure all NO-areas exist even when missing in data
for feature in geojson_data["features"]:
    area = feature["properties"]["ElSpotOmr"]
    if area not in means:
        means[area] = np.nan

st.session_state.area_means = means

# ------------------------------------------------------------------------------
# Color scale
# ------------------------------------------------------------------------------
vals = [v for v in means.values() if not pd.isna(v)]

if len(vals) == 0:
    vmin, vmax = 0, 1
else:
    vmin, vmax = min(vals), max(vals)

def get_color(value):
    if pd.isna(value):
        return "#cccccc"   # grey for missing
    if vmin == vmax:
        norm = 0.5
    else:
        norm = (value - vmin) / (vmax - vmin)
        norm = min(max(norm, 0), 1)
    r = int(255 * (1 - norm))
    g = int(255 * norm)
    return f"#{r:02x}{g:02x}00"

# ------------------------------------------------------------------------------
# Create the map
# ------------------------------------------------------------------------------
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

def style_function(feature):
    area = feature["properties"]["ElSpotOmr"]
    val = means.get(area, np.nan)
    fill = get_color(val)

    if st.session_state.selected_area == area:
        return {
            "fillColor": fill,
            "color": "red",
            "weight": 3,
            "fillOpacity": 0.6
        }
    return {
        "fillColor": fill,
        "color": "blue",
        "weight": 1,
        "fillOpacity": 0.4
    }

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["ElSpotOmr"],
        aliases=["Price area:"]
    )
).add_to(m)

# Marker for clicked point
if st.session_state.clicked_point:
    folium.Marker(
        st.session_state.clicked_point,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

map_data = st_folium(m, width=900, height=600)

# ------------------------------------------------------------------------------
# Click handler
# ------------------------------------------------------------------------------
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state.clicked_point = (lat, lon)

    point = Point(lon, lat)
    clicked_area = None

    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            clicked_area = feature["properties"]["ElSpotOmr"]
            break

    st.session_state.selected_area = clicked_area
    st.rerun()

# ------------------------------------------------------------------------------
# Display values
# ------------------------------------------------------------------------------
st.write("### Mean quantity (kWh) per NO area:")
st.json(means)

if st.session_state.selected_area:
    st.success(f"Selected area: **{st.session_state.selected_area}**")
