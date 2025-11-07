import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    n_std = st.slider("Number of standard deviations", 1.0, 6.0, 3.0, step=0.5)

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

    # --- Changed from MAD to standard deviation ---
    mean_satv = np.mean(satv)
    std_satv = np.std(satv)
    ucl = mean_satv + n_std * std_satv
    lcl = mean_satv - n_std * std_satv
    # ------------------------------------------------

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

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Outlier Summary")
    st.markdown(f"**Number of outliers:** {len(outliers)}")
    st.dataframe(outliers[["time", "temperature_2m", "SATV", "UCL", "LCL"]].head(10))


# ANOMALY / LOF TAB
with tab_lof:
    st.subheader("Precipitation — Local Outlier Factor (LOF)")

    # --- UI controls ---
    outlier_frac = st.slider("Proportion of outliers", 0.001, 0.1, 0.01, step=0.01)

    # --- Prepare data ---
    precip = df["precipitation"].fillna(0).astype(float)
    # Smooth short-term noise (3-hour rolling mean)
    smoothed = precip.rolling(window=3, min_periods=1).mean()
    # Log-transform to reduce effect of large spikes
    X = np.log1p(smoothed.values.reshape(-1, 1))

    # --- Fit LOF (density-based anomaly detection) ---
    if len(X) > 10:
        n_neighbors = max(5, min(20, len(X) // 10))
        lof = LocalOutlierFactor(n_neighbors=n_neighbors)
        lof.fit(X)
        scores = -lof.negative_outlier_factor_

        # Compute threshold based on chosen fraction
        threshold = np.quantile(scores, 1 - outlier_frac)
        df["anomaly"] = scores > threshold
    else:
        df["anomaly"] = False
        st.warning("Not enough data for LOF analysis.")

    anomalies = df[df["anomaly"]]

    # --- Plot results ---
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df["time"], y=precip,
        mode="lines", name="Precipitation (mm)",
        line=dict(width=1.2, color="blue"),
        hovertemplate="%{x}<br>Precip: %{y:.2f} mm<extra></extra>"
    ))

    fig2.add_trace(go.Scatter(
        x=anomalies["time"], y=anomalies["precipitation"],
        mode="markers", name=f"Anomalies ({len(anomalies)})",
        marker=dict(color="red", size=6, symbol="x"),
        hovertemplate="Outlier<br>%{x}<br>Precip: %{y:.2f} mm<extra></extra>"
    ))

    fig2.update_layout(
        title=f"Precipitation — LOF Anomaly Detection ({city}, {year})",
        xaxis_title="Time", yaxis_title="Precipitation (mm)",
        template="plotly_white",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(fig2, use_container_width=True)

    # --- Anomaly summary ---
    st.markdown("### Anomaly Summary")
    st.markdown(f"**Number of anomalies:** {len(anomalies)}")
    st.dataframe(anomalies[["time", "precipitation"]].head(10))

