import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta

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
means_df = df_period.groupby("pricearea")["quantitykwh"].mean().reset_index()
means_dict = dict(zip(means_df["pricearea"], means_df["quantitykwh"]))
st.session_state.area_means = means_dict

if means_df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# ==============================================================================
# Create the map with Choropleth
# ==============================================================================
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

# Force a visible gradient
vmin = means_df["quantitykwh"].min()
vmax = means_df["quantitykwh"].max()
thresholds = np.linspace(vmin, vmax, 6).tolist()

folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=means_df,
    columns=["pricearea", "quantitykwh"],
    key_on="feature.properties.ElSpotOmr",
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f"{data_type} mean quantity (kWh)",
    threshold_scale=thresholds,
    nan_fill_color="lightgray"
).add_to(m)

# Add tooltip with actual values
def tooltip_function(feature):
    area = normalize_area_name(feature["properties"]["ElSpotOmr"])
    value = means_dict.get(area, None)
    if value is None or pd.isna(value):
        return f"{area}: No data"
    return f"{area}: {value:.2f} kWh"

folium.GeoJson(
    geojson_data,
    tooltip=folium.GeoJsonTooltip(
        fields=["ElSpotOmr"],
        aliases=["Price area:"],
        labels=True,
        sticky=True
    )
).add_to(m)

# Marker for clicked point
if st.session_state.clicked_point:
    folium.Marker(
        st.session_state.clicked_point,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

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
st.dataframe(means_df)

if st.session_state.selected_area:
    val = st.session_state.area_means.get(st.session_state.selected_area, None)
    if val is not None:
        st.success(f"Selected area: **{st.session_state.selected_area}** → {val:.2f} kWh")
    else:
        st.success(f"Selected area: **{st.session_state.selected_area}** (no data)")

st.write(f"Clicked coordinates: {st.session_state.clicked_point}")
