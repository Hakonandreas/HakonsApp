import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta
from branca.element import Element

from functions.elhub_utils import load_elhub_data, load_elhub_consumption

st.set_page_config(layout="wide")
st.title("Energy Map – Norway Price Areas (NO1–NO5)")

# ==============================================================================
# Load GeoJSON
# ==============================================================================
geojson_path = Path(__file__).parent / "data" / "ElSpot_omraade.geojson"
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

def normalize_area_name(name):
    if isinstance(name, str) and name.startswith("N0") and len(name) == 3:
        return "NO" + name[-1]
    return name

def extract_area_name(feature):
    raw = feature["properties"].get("ElSpotOmr")
    return normalize_area_name(raw)

# ==============================================================================
# Session state
# ==============================================================================
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None
if "area_means" not in st.session_state:
    st.session_state.area_means = {}

# ==============================================================================
# UI – choose Production / Consumption
# ==============================================================================
data_type = st.radio("Select data type:", ["Production", "Consumption"], horizontal=True)

if data_type == "Production":
    df = load_elhub_data()
    group_col = "productiongroup"
else:
    df = load_elhub_consumption()
    group_col = "consumptiongroup"

groups = sorted(df[group_col].dropna().unique().tolist())
group = st.selectbox("Select group:", groups)
days = st.slider("Time interval (days):", 1, 30, 7)

# ==============================================================================
# Prepare filtered dataframe
# ==============================================================================
df = df.copy()
df["starttime"] = pd.to_datetime(df["starttime"])
df["pricearea"] = df["pricearea"].apply(normalize_area_name)

end_time = df["starttime"].max()
start_time = end_time - timedelta(days=days)

df_period = df[
    (df["starttime"] >= start_time) &
    (df["starttime"] <= end_time) &
    (df[group_col] == group)
]

# ==============================================================================
# Compute mean per price area
# ==============================================================================
means = df_period.groupby("pricearea")["quantitykwh"].mean().to_dict()

for feature in geojson_data["features"]:
    area = extract_area_name(feature)
    if area not in means:
        means[area] = np.nan

st.session_state.area_means = means

# ==============================================================================
# Color scale
# ==============================================================================
vals = [v for v in means.values() if not pd.isna(v)]
vmin, vmax = (0, 1) if len(vals) == 0 else (min(vals), max(vals))

def get_color(value):
    if pd.isna(value):
        return "#cccccc"
    if vmin == vmax:
        norm = 0.5
    else:
        norm = (value - vmin) / (vmax - vmin)
        norm = min(max(norm, 0), 1)
    r = int(255 * (1 - norm))
    g = int(255 * norm)
    return f"#{r:02x}{g:02x}00"

# ==============================================================================
# Create the map
# ==============================================================================
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

def style_function(feature):
    area = extract_area_name(feature)
    val = means.get(area, np.nan)
    fill = get_color(val)

    if st.session_state.selected_area == area:
        return {"fillColor": fill, "color": "red", "weight": 3, "fillOpacity": 0.6}
    return {"fillColor": fill, "color": "blue", "weight": 1, "fillOpacity": 0.4}

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["ElSpotOmr"], aliases=["Price area:"])
).add_to(m)

# Marker for clicked point
if st.session_state.clicked_point:
    folium.Marker(
        st.session_state.clicked_point,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# ==============================================================================
# Add legend (no macro, pure HTML)
# ==============================================================================
legend_html = f"""
<div style="
    position: fixed;
    bottom: 50px;
    left: 50px;
    width: 160px;
    height: 190px;
    background-color: white;
    border:2px solid grey;
    z-index:9999;
    font-size:14px;
    padding: 10px;
    ">
    <b>{data_type} scale (kWh)</b><br>
    <i style="background:{get_color(vmin)};width:20px;height:10px;display:inline-block;"></i> {vmin:.1f}<br>
    <i style="background:{get_color(vmin + (vmax - vmin) * 0.2)};width:20px;height:10px;display:inline-block;"></i> {(vmin + (vmax - vmin) * 0.2):.1f}<br>
    <i style="background:{get_color(vmin + (vmax - vmin) * 0.4)};width:20px;height:10px;display:inline-block;"></i> {(vmin + (vmax - vmin) * 0.4):.1f}<br>
    <i style="background:{get_color(vmin + (vmax - vmin) * 0.6)};width:20px;height:10px;display:inline-block;"></i> {(vmin + (vmax - vmin) * 0.6):.1f}<br>
    <i style="background:{get_color(vmin + (vmax - vmin) * 0.8)};width:20px;height:10px;display:inline-block;"></i> {(vmin + (vmax - vmin) * 0.8):.1f}<br>
    <i style="background:{get_color(vmax)};width:20px;height:10px;display:inline-block;"></i> {vmax:.1f}
</div>
"""

m.get_root().html.add_child(Element(legend_html))

# ==============================================================================
# Click handler
# ==============================================================================
map_data = st_folium(m, width=950, height=630)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state.clicked_point = (lat, lon)

    point = Point(lon, lat)
    clicked_area = None

    for feature in geojson_data["features"]:
        geom = shape(feature["geometry"])
        if isinstance(geom, (Polygon, MultiPolygon)) and geom.contains(point):
            clicked_area = extract_area_name(feature)
            break

    st.session_state.selected_area = clicked_area
    st.rerun()

# ==============================================================================
# Display values
# ==============================================================================
st.write("### Mean quantity (kWh) per NO area:")
st.json(means)

if st.session_state.selected_area:
    st.success(f"Selected area: **{st.session_state.selected_area}**")

st.write(f"Clicked coordinates: {st.session_state.clicked_point}")
