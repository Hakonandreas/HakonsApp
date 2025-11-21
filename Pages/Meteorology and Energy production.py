import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from functions.Snow_drift import calculate_snow_drift, plot_wind_rose
from functions.weather_utils import download_era5_data


st.title("❄️ Snow Drift Explorer")

# Check if coordinates are available
if "clicked_point" not in st.session_state or st.session_state.clicked_point is None:
    st.warning("No coordinates selected on the map page. Please go back and click a location.")
    st.stop()

lat, lon = st.session_state.clicked_point
st.write(f"Using coordinates: {lat:.3f}, {lon:.3f}")

# Year range selector
start_year, end_year = st.slider(
    "Select year range",
    min_value=2000, max_value=2025,
    value=(2015, 2020)
)

# Define July–June year boundaries
years = range(start_year, end_year + 1)
results = []

for y in years:
    start_date = pd.Timestamp(year=y, month=7, day=1)
    end_date = pd.Timestamp(year=y+1, month=6, day=30)
    drift = calculate_snow_drift(lat, lon, start_date, end_date)
    results.append({"year": f"{y}-{y+1}", "snow_drift": drift})

df = pd.DataFrame(results)

# Plot snow drift per year
st.write("### Annual Snow Drift (July–June)")
st.bar_chart(df.set_index("year"))

# Plot wind rose
st.write("### Wind Rose")
fig = plot_wind_rose(lat, lon, start_year, end_year)
st.pyplot(fig)
