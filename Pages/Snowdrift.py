import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from functions import get_city_from_area, download_era5_data

# ---- Snowdrift formulas copied from Snow_drift.py ----

def snow_drift_index(temp, wind, precip):
    """Original formula from Snow_drift.py"""
    drift = 0

    # Only snow if temperature is below freezing
    if temp <= 0:
        drift = precip * (wind ** 2)

    return drift


def compute_snow_drift(df):
    """
    Apply snow drift formula to an ERA5 dataframe.
    Requires: temperature_2m, wind_speed_10m, precipitation
    """
    df = df.copy()
    df["snow_drift"] = df.apply(
        lambda row: snow_drift_index(
            row["temperature_2m"],
            row["wind_speed_10m"],
            row["precipitation"]
        ),
        axis=1
    )
    return df


def plot_wind_rose(df):
    """
    Wind rose using wind direction + wind speed.
    Compatible with Snow_drift.py version.
    """
    ax = WindroseAxes.from_ax()
    ax.bar(
        df["wind_direction_10m"],
        df["wind_speed_10m"],
        normed=True,
        opening=0.8,
        edgecolor='white'
    )
    ax.set_legend()
    st.pyplot(plt)

def extract_july_to_june(df, year):
    start = pd.Timestamp(year=year, month=7, day=1, tz="Europe/Oslo")
    end = pd.Timestamp(year=year+1, month=6, day=30, tz="Europe/Oslo")
    return df[(df["time"] >= start) & (df["time"] <= end)]


st.title("Snow Drift Analysis")

# --- Check if map selection exists ---
if "latitude" not in st.session_state or "longitude" not in st.session_state:
    st.error("No map selection found. Please select a location on the map page.")
    st.stop()

lat = st.session_state["latitude"]
lon = st.session_state["longitude"]

# --- Year range selection ---
start_year = st.number_input("Start year", min_value=1980, max_value=2024, value=2020)
end_year = st.number_input("End year", min_value=1980, max_value=2024, value=2023)

if start_year > end_year:
    st.error("Start year must be <= end year.")
    st.stop()

# --- Loop over years ---
year_values = []

for year in range(start_year, end_year + 1):

    # Download ERA5 for July–Dec of selected year AND Jan–June next year
    df1 = download_era5_data(lat, lon, year)
    df2 = download_era5_data(lat, lon, year + 1)
    df_all = pd.concat([df1, df2], ignore_index=True)

    # Extract July–June year block
    df_period = extract_july_to_june(df_all, year)

    # Compute snow drift
    df_sd = compute_snow_drift(df_period)

    # Sum snow drift for the year
    total_drift = df_sd["snow_drift"].sum()
    year_values.append(total_drift)

# --- Plot snow drift per “snow year” ---
st.subheader("Total Snow Drift Per Year")

plot_data = pd.DataFrame({"year": range(start_year, end_year + 1),
                          "snow_drift": year_values})
st.bar_chart(plot_data, x="year", y="snow_drift")

# --- Wind rose for the LAST selected year ---
st.subheader(f"Wind Rose for {end_year}–{end_year+1}")

df1 = download_era5_data(lat, lon, end_year)
df2 = download_era5_data(lat, lon, end_year + 1)
df_all = pd.concat([df1, df2], ignore_index=True)

df_period = extract_july_to_june(df_all, end_year)
plot_wind_rose(df_period)
