import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram
from functions.weather_utils import get_city_from_area, download_era5_data

st.title("Weather Data Analysis — STL & Spectrogram")


# Check chosen area
chosen_area = st.session_state.get("chosen_area")
if not chosen_area:
    st.warning("Please select a price area on the main page first.")
    st.stop()

city, lat, lon = get_city_from_area(chosen_area)
year = 2021

# --------------------------------------
# Download ERA5 data
# --------------------------------------
st.info(f"Fetching ERA5 data for **{city}** ({lat:.2f}, {lon:.2f}) in {year}...")
df = download_era5_data(lat, lon, year)
df["month"] = df["time"].dt.to_period("M").astype(str)
st.success(f"✅ Data loaded for {city} ({chosen_area})")

# --------------------------------------
# Sidebar: Select parameter and month
# --------------------------------------
columns = [c for c in df.columns if c not in ["time", "month"]]
param = st.selectbox("Select weather parameter for analysis:", columns)

months = sorted(df["month"].unique())
month_choice = st.select_slider("Select month:", options=months, value=months[0])

df_filtered = df[df["month"] == month_choice].set_index("time")
ts = df_filtered[param]

# Resample hourly to handle any irregularities
ts = ts.resample("H").mean().interpolate()

# --------------------------------------
# Tabs
# --------------------------------------
tab1, tab2 = st.tabs(["STL Decomposition", "Spectrogram"])

# --- STL Decomposition Tab ---
with tab1:
    st.subheader(f"STL Decomposition — {param} ({month_choice})")

    # User can set STL parameters optionally
    period = st.number_input("Seasonal period (hours):", min_value=1, value=24)
    seasonal = st.number_input("Seasonal smoothing:", min_value=1, value=13)
    trend = st.number_input("Trend smoothing (odd number):", min_value=1, value=53)
    robust = st.checkbox("Robust decomposition", value=True)

    stl = STL(ts, period=period, seasonal=seasonal, trend=trend, robust=robust)
    res = stl.fit()

    # Separate plots for each component
    components = {
        "Observed": ts,
        "Trend": res.trend,
        "Seasonal": res.seasonal,
        "Residual": res.resid
    }

    for name, series in components.items():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=series.values, name=name, line=dict(color="blue")))
        fig.update_layout(title=name, xaxis_title="Time", yaxis_title=param)
        st.plotly_chart(fig, use_container_width=True)

# --- Spectrogram Tab ---
with tab2:
    st.subheader(f"Spectrogram — {param} ({month_choice})")
    f, t, Sxx = spectrogram(ts.values, fs=1)  # hourly frequency = 1
    fig = go.Figure(data=go.Heatmap(
        z=Sxx,
        x=t,
        y=f,
        colorscale="Viridis"
    ))
    fig.update_layout(
        title="Spectrogram",
        xaxis_title="Time (hours)",
        yaxis_title="Frequency (1/hour)"
    )
    st.plotly_chart(fig, use_container_width=True)
