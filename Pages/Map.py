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
# Normalize function for GeoJSON and dataframe keys
# ==============================================================================
def normalize_area_name(name):
    if isinstance(name, str) and name.startswith("N0") and len(name) == 3:
        return "NO" + name[-1]
    return name

# ==============================================================================
# Load GeoJSON and inject normalized keys
# ==============================================================================
geojson_path = Path(__file__).parent / "data" / "ElSpot_omraade.geojson"
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

for feature in geojson_data["features"]:
    raw_name = feature["properties"].get("ElSpotOmr")
    feature["properties"]["ElSpotOmrNorm"] = normalize_area_name(raw_name)

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
means_df = df_period.groupby("pricearea", as_index=False)["quantitykwh"].mean()
means_dict = dict(zip(means_df["pricearea"], means_df["quantitykwh"]))
st.session_state.area_means = means_dict

if means_df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# ==============================================================================
# Create map
# ==============================================================================
geojson_keys = {feature["properties"]["ElSpotOmrNorm"] for feature in geojson_data["features"]}
data_keys = set(means_df["pricearea"])

st.write("GeoJSON keys:", geojson_keys)
st.write("Data keys:", data_keys)


m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

# Thresholds for choropleth
vmin = means_df["quantitykwh"].min()
vmax = means_df["quantitykwh"].max()
if np.isclose(vmin, vmax):
    thresholds = [vmin - 1e-6, vmin, vmax + 1e-6]
else:
    thresholds = np.linspace(vmin, vmax, 6).tolist()

# Choropleth layer
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=means_df,
    columns=["pricearea", "quantitykwh"],
    key_on="feature.properties.ElSpotOmrNorm",
    fill_color="YlGnBu",
    fill_opacity=0.6,
    line_opacity=0.3,
    line_color="black",
    legend_name=f"{data_type} mean quantity (kWh)",
    threshold_scale=thresholds,
    nan_fill_color="lightgray"
).add_to(m)

# Tooltip layer
folium.GeoJson(
    geojson_data,
    name="tooltips",
    tooltip=folium.GeoJsonTooltip(
        fields=["ElSpotOmrNorm"],
        aliases=["Price area:"],
        labels=True,
        sticky=True
    ),
    style_function=lambda _: {"color": "transparent", "weight": 0, "fillOpacity": 0}
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
            clicked_area = feature["properties"]["ElSpotOmrNorm"]
            break

    if clicked_area != st.session_state.selected_area:
        st.session_state.selected_area = clicked_area
        st.rerun()

# ==============================================================================
# Highlight selected area
# ==============================================================================
if st.session_state.selected_area:
    def highlight_style(feat):
        is_sel = feat["properties"]["ElSpotOmrNorm"] == st.session_state.selected_area
        if is_sel:
            return {"color": "#d62728", "weight": 4, "fillOpacity": 0}
        return {"color": "transparent", "weight": 0, "fillOpacity": 0}

    folium.GeoJson(
        geojson_data,
        name="selected_highlight",
        style_function=highlight_style,
        tooltip=None,
    ).add_to(m)
    map_data = st_folium(m, width=950, height=630)

# ==============================================================================
# Display values
# ==============================================================================
st.write("### Mean quantity (kWh) per NO area:")
st.dataframe(means_df)

if st.session_state.selected_area:
    val = st.session_state.area_means.get(st.session_state.selected_area, None)
    if val is not None and not pd.isna(val):
        st.success(f"Selected area: **{st.session_state.selected_area}** → {val:.2f} kWh")
    else:
        st.success(f"Selected area: **{st.session_state.selected_area}** (no data)")

st.write(f"Clicked coordinates: {st.session_state.clicked_point}")
