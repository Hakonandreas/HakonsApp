import streamlit as st
import json
from shapely.geometry import shape, Point
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# --- Load GeoJSON with cache ---
@st.cache_data
def load_geojson():
    with open('data/ElSpot_omraade.geojson', "r", encoding="utf-8") as f:
        return json.load(f)

geojson_data = load_geojson()

st.title("Norway Price Areas Map (NO1-NO5)")

# --- Initialize session state ---
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

# --- Function to find which area contains a point ---
def find_price_area(lat, lon):
    point = Point(lon, lat)  # GeoJSON uses (lon, lat)
    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            return feature["properties"].get("ElSpotOmr", "Unknown")
    return None

# --- Create base Plotly map ---
fig = px.choropleth_mapbox(
    geojson=geojson_data,
    locations=[f["properties"].get("ElSpotOmr", f["id"]) for f in geojson_data["features"]],
    featureidkey="properties.ElSpotOmr",
    color=[0]*len(geojson_data["features"]),  # dummy color
    center={"lat": 63.0, "lon": 10.5},
    zoom=5.5,
    mapbox_style="carto-positron",
)

# --- Highlight selected area ---
if st.session_state.selected_area:
    selected_feature = [
        f for f in geojson_data["features"]
        if f["properties"].get("ElSpotOmr") == st.session_state.selected_area
    ][0]
    fig.add_trace(go.Choroplethmapbox(
        geojson={"type": "FeatureCollection", "features": [selected_feature]},
        locations=[st.session_state.selected_area],
        z=[1],
        colorscale=[[0, "yellow"], [1, "yellow"]],
        marker_line_color="red",
        marker_line_width=3,
        showscale=False,
        hoverinfo="skip"
    ))

# --- Add clicked point marker ---
if st.session_state.clicked_point:
    lat, lon = st.session_state.clicked_point
    fig.add_trace(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=go.scattermapbox.Marker(size=12, color="red"),
        name="Clicked Point"
    ))

# --- Display map and capture clicks ---
clicked_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=600,
    override_width="100%"
)

# --- Update session state if clicked ---
if clicked_points:
    lat = clicked_points[0]["lat"]
    lon = clicked_points[0]["lon"]
    st.session_state.clicked_point = (lat, lon)
    st.session_state.selected_area = find_price_area(lat, lon)
    st.experimental_rerun()  # refresh to show marker & highlight

# --- Display info ---
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")
