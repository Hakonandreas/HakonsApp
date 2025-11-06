import streamlit as st
import pandas as pd
import plotly.express as px
from functions.weather_utils import get_city_from_area, download_era5_data

st.title("Weather Data Explorer")

# --------------------------------------
# Check if a price area is selected
# --------------------------------------
chosen_area = st.session_state.get("chosen_area", None)

if not chosen_area:
    st.warning("Please select a price area on the main page first.")
    st.stop()

# --------------------------------------
# Download ERA5 data using the shared helper
# --------------------------------------
city, lat, lon = get_city_from_area(chosen_area)
year = 2021

st.info(f"Fetching ERA5 data for **{city}** ({lat:.2f}, {lon:.2f}) in {year}...")

df = download_era5_data(lat, lon, year)

# --------------------------------------
# Prepare data
# --------------------------------------
df["month"] = df["time"].dt.to_period("M").astype(str)
st.success(f"✅ Data loaded for {city} ({chosen_area})")

# --------------------------------------
# Variable and month selection
# --------------------------------------
columns = [c for c in df.columns if c not in ["time", "month"]]

st.write("Select weather parameters to plot:")
selected_cols = [col for col in columns if st.checkbox(col, value=(col == columns[0]))]

months = sorted(df["month"].unique())
month_choice = st.select_slider("Select month:", options=months, value=months[0])

# --------------------------------------
# Filter and plot
# --------------------------------------
df_filtered = df[df["month"] == month_choice]

if selected_cols:
    fig = px.line(
        df_filtered,
        x="time",
        y=selected_cols,
        title=f"Weather data for {city} - {month_choice}",
        labels={"value": "Value", "time": "Time", "variable": "Parameter"}
    )
    fig.update_layout(xaxis_title="Time", yaxis_title="Value")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Please select at least one variable to plot.")

