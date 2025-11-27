import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from functions import download_era5_data
from functions.elhub_utils import load_elhub_data, load_elhub_consumption


# ============================================================
# METEOROLOGY DATA (ERA5)
# ============================================================

@st.cache_data(show_spinner=True)
def load_meteorology_data(latitude: float, longitude: float, year: int) -> pd.DataFrame:
    """Wrapper around your ERA5 downloader."""
    df = download_era5_data(latitude, longitude, year)

    rename_map = {
        "temperature_2m": "temperature",
        "precipitation": "precipitation",
        "wind_speed_10m": "wind_speed",
        "wind_gusts_10m": "wind_gusts",
        "wind_direction_10m": "wind_direction",
        "time": "time"
    }
    df = df.rename(columns=rename_map)
    df = df.sort_values("time").reset_index(drop=True)
    return df


# ============================================================
# ENERGY DATA (PRODUCTION + CONSUMPTION)
# ============================================================

@st.cache_data(show_spinner=True)
def load_production():
    df = load_elhub_data()
    df = df.rename(columns={"starttime": "time"})
    df = df.sort_values("time")
    return df

@st.cache_data(show_spinner=True)
def load_consumption():
    df = load_elhub_consumption()
    df = df.rename(columns={"starttime": "time"})
    df = df.sort_values("time")
    return df


# ============================================================
# CORRELATION FUNCTIONS
# ============================================================

def sliding_window_correlation(df, var_x, var_y, window_size):
    results = []
    df = df.dropna(subset=[var_x, var_y]).copy()
    df = df.sort_values("time")

    for i in range(len(df) - window_size + 1):
        window = df.iloc[i:i + window_size]
        corr = window[var_x].corr(window[var_y])
        results.append({"time": window["time"].iloc[-1], "correlation": corr})

    return pd.DataFrame(results)


def compute_lagged_correlation(df, var_x, var_y, max_lag_hours):
    correlations = []
    for lag in range(-max_lag_hours, max_lag_hours + 1):
        shifted = df[var_x].shift(lag)
        corr = shifted.corr(df[var_y])
        correlations.append({"lag_hours": lag, "correlation": corr})

    return pd.DataFrame(correlations)


# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🌤️ Meteorology & ⚡ Energy Correlation Explorer")

st.sidebar.header("Data Settings")

# ----------------------------
# SELECT ENERGY DATASET (PROD/CONS)
# ----------------------------
energy_type = st.sidebar.selectbox(
    "Energy dataset",
    ["Production", "Consumption"]
)

if energy_type == "Production":
    energy_df = load_production()
else:
    energy_df = load_consumption()


# ----------------------------
# METEOROLOGY PARAMETERS
# ----------------------------
st.sidebar.subheader("Meteorology Parameters")

latitude = st.sidebar.number_input("Latitude", value=60.10)
longitude = st.sidebar.number_input("Longitude", value=10.75)
year = st.sidebar.number_input("Year", value=2024)

with st.spinner("Loading meteorology data ..."):
    met_df = load_meteorology_data(latitude, longitude, int(year))


# ----------------------------
# MERGE DATASETS
# ----------------------------
met_df["time"] = pd.to_datetime(met_df["time"])
energy_df["time"] = pd.to_datetime(energy_df["time"])

df = pd.merge_asof(
    energy_df.sort_values("time"),
    met_df.sort_values("time"),
    on="time",
    direction="nearest",
    tolerance=pd.Timedelta("30min")
)

st.success("Data loaded and merged successfully!")


# ============================================================
# VARIABLE SELECTION
# ============================================================

st.header("Variable Selection")

met_vars = ["temperature", "precipitation", "wind_speed", "wind_gusts", "wind_direction"]
energy_vars = [col for col in energy_df.columns if col not in ["time", "_id"]]

var_x = st.selectbox("Meteorological variable", met_vars)
var_y = st.selectbox("Energy variable", energy_vars)


# ============================================================
# SLIDING WINDOW CORRELATION
# ============================================================

st.header("Sliding Window Correlation")

window_size = st.slider("Window size (hours)", 12, 240, 72)

corr_df = sliding_window_correlation(df, var_x, var_y, window_size)

fig1 = px.line(
    corr_df,
    x="time", y="correlation",
    title=f"Sliding Window Correlation: {var_x} vs {var_y}"
)
st.plotly_chart(fig1, use_container_width=True)


# ============================================================
# LAGGED CORRELATION
# ============================================================

st.header("Lagged Correlation Analysis")

max_lag = st.slider("Max lag (hours)", 1, 72, 24)

lag_df = compute_lagged_correlation(df, var_x, var_y, max_lag)

fig2 = px.line(
    lag_df,
    x="lag_hours", y="correlation",
    title=f"Lagged Correlation: {var_x} → {var_y}"
)
st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# RAW DATA PREVIEW
# ============================================================

with st.expander("Show merged dataset"):
    st.dataframe(df)
