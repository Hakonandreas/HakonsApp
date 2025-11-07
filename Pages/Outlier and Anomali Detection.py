import streamlit as st
import pandas as pd
import plotly.express as px
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
from functions.weather_utils import get_city_from_area, download_era5_data

st.title("Outlier and Anomaly Detection")

# Use the chosen area from session_state
chosen_area = st.session_state.get("chosen_area", None)

city, lat, lon = get_city_from_area(chosen_area)
year = 2021

# Load ERA5 data
st.info(f"Fetching ERA5 data for **{city} ({chosen_area})** — {year}")
df = download_era5_data(lat, lon, year)
df["time"] = pd.to_datetime(df["time"])

# Create tabs
tab_spc, tab_lof = st.tabs(["📈 Outlier / SPC Analysis", "💧 Anomaly / LOF Analysis"])

# OUTLIER / SPC TAB
with tab_spc:
    st.subheader("Seasonally Adjusted Temperature Variation (SPC)")

    # UI controls
    cutoff_frac = st.slider("DCT frequency cut-off fraction", 0.001, 0.05, 0.01, step=0.001)
    n_std = st.slider("Number of MAD deviations", 1.0, 6.0, 3.0, step=0.5)

    # Run analysis
    temp = df["temperature_2m"].values
    temp_dct = dct(temp, norm='ortho')
    cutoff = int(len(temp) * cutoff_frac)

    temp_dct_low = np.copy(temp_dct)
    temp_dct_low[cutoff:] = 0
    trend = idct(temp_dct_low, norm='ortho')

    satv = temp - trend
    df["SATV"] = satv
    df["Trend"] = trend

    median_satv = np.median(satv)
    mad_satv = np.median(np.abs(satv - median_satv))
    ucl = median_satv + n_std * mad_satv
    lcl = median_satv - n_std * mad_satv

    df["UCL"] = df["Trend"] + ucl
    df["LCL"] = df["Trend"] + lcl
    df["outlier"] = (df["temperature_2m"] > df["UCL"]) | (df["temperature_2m"] < df["LCL"])
    outliers = df[df["outlier"]]

    # Plot
    fig = px.line(df, x="time", y="temperature_2m",
                  title=f"Temperature — SPC Outlier Detection ({city}, {year})",
                  labels={"temperature_2m": "Temperature (°C)"})

    fig.add_scatter(x=df["time"], y=df["UCL"], mode="lines",
                    name="UCL", line=dict(color="red", dash="dash"))
    fig.add_scatter(x=df["time"], y=df["LCL"], mode="lines",
                    name="LCL", line=dict(color="red", dash="dash"))
    fig.add_scatter(x=outliers["time"], y=outliers["temperature_2m"],
                    mode="markers", name="Outliers",
                    marker=dict(color="red", size=6, symbol="x"))

    st.plotly_chart(fig, width="stretch")

    st.markdown("### Outlier Summary")
    st.markdown(f"**Number of outliers:** {len(outliers)}")
    st.dataframe(outliers[["time", "temperature_2m", "SATV", "UCL", "LCL"]].head(10))


# ANOMALY / LOF TAB
with tab_lof:
    st.subheader("Precipitation — Local Outlier Factor (LOF)")

    # UI controls
    outlier_frac = st.slider("Proportion of outliers", 0.001, 0.1, 0.01, step=0.005)

    values = df[["precipitation"]].values
    lof = LocalOutlierFactor(n_neighbors=20, contamination=outlier_frac)
    outlier_labels = lof.fit_predict(values)

    df["anomaly"] = outlier_labels == -1
    anomalies = df[df["anomaly"]]

    # Plot
    fig2 = px.line(df, x="time", y="precipitation",
                   title=f"Precipitation — LOF Anomaly Detection ({city}, {year})",
                   labels={"precipitation": "Precipitation (mm)"})

    fig2.add_scatter(x=anomalies["time"], y=anomalies["precipitation"],
                     mode="markers", name="Anomalies",
                     marker=dict(color="red", size=6, symbol="x"))

    st.plotly_chart(fig2, width="stretch")

    st.markdown("### Anomaly Summary")
    st.markdown(f"**Number of anomalies:** {len(anomalies)}")
    st.dataframe(anomalies[["time", "precipitation"]].head(10))
