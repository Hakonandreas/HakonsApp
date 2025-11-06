import streamlit as st
import pandas as pd
from statsmodels.tsa.seasonal import STL
import plotly.graph_objects as go
from functions.elhub_utils import load_elhub_data  # your shared utility

st.title("Production Data Analysis")

# Tabs for STL and Spectrogram
tab1, tab2 = st.tabs(["📈 STL Decomposition", "🎛 Spectrogram"])

# Load Elhub data once
df = load_elhub_data()


# TAB 1: STL DECOMPOSITION
with tab1:
    st.subheader("STL Decomposition (Seasonal-Trend using LOESS)")

    # User input
    pricearea = st.selectbox("Select price area:", sorted(df["pricearea"].unique()))
    productiongroup = st.selectbox("Select production group:", sorted(df["productiongroup"].unique()))
    period = st.number_input("Period (hours)", value=24 * 7)
    seasonal = st.number_input("Seasonal smoother", value=13)
    trend = st.number_input("Trend smoother", value=int(period * 2 + 1))
    robust = st.checkbox("Robust fitting", value=True)

    # Filter and prepare data
    df_filtered = df[
        (df["pricearea"] == pricearea) & (df["productiongroup"] == productiongroup)
    ]
    df_filtered = (
        df_filtered.set_index("starttime")[["quantitykwh"]]
        .resample("H")
        .mean()
        .interpolate()
    )

    if df_filtered.empty:
        st.warning("No data found for the selected combination.")
    else:
        # Perform STL decomposition
        stl = STL(
            df_filtered["quantitykwh"],
            period=period,
            seasonal=seasonal,
            trend=trend,
            robust=robust,
        )
        res = stl.fit()

        # Create Plotly figure with 4 subplots
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
        )

        # Observed
        fig.add_trace(
            go.Scatter(
                x=df_filtered.index,
                y=df_filtered["quantitykwh"],
                name="Observed",
                line=dict(color="steelblue"),
            ),
            row=1,
            col=1,
        )

        # Trend
        fig.add_trace(
            go.Scatter(
                x=df_filtered.index,
                y=res.trend,
                name="Trend",
                line=dict(color="royalblue"),
            ),
            row=2,
            col=1,
        )

        # Seasonal
        fig.add_trace(
            go.Scatter(
                x=df_filtered.index,
                y=res.seasonal,
                name="Seasonal",
                line=dict(color="seagreen"),
            ),
            row=3,
            col=1,
        )

        # Residual
        fig.add_trace(
            go.Scatter(
                x=df_filtered.index,
                y=res.resid,
                name="Residual",
                mode="markers",
                marker=dict(color="firebrick", size=4),
            ),
            row=4,
            col=1,
        )

        # Layout adjustments
        fig.update_layout(
            height=800,
            title=f"STL Decomposition — {productiongroup} ({pricearea})",
            showlegend=False,
            template="plotly_white",
        )
        fig.update_xaxes(title_text="Date", row=4, col=1)
        fig.update_yaxes(title_text="kWh")

        st.plotly_chart(fig, use_container_width=True)


# TAB 2: SPECTROGRAM
with tab2:
    st.subheader("Spectrogram of Production Data")

    pricearea = st.selectbox("Price area:", sorted(df["pricearea"].unique()), key="spec_area")
    productiongroup = st.selectbox("Production group:", sorted(df["productiongroup"].unique()), key="spec_group")
    window_length = st.number_input("Window length (hours)", value=168)
    overlap = st.slider("Overlap fraction", 0.0, 0.9, 0.5, 0.1)

    # Filter and prepare data
    df_filtered = df[(df["pricearea"] == pricearea) & (df["productiongroup"] == productiongroup)]
    df_filtered = df_filtered.set_index("starttime")[["quantitykwh"]].resample("H").mean().interpolate()

    if df_filtered.empty:
        st.warning("No data found for the selected combination.")
    else:
        signal = df_filtered["quantitykwh"].values
        fs = 1.0  # samples/hour
        nperseg = int(window_length)
        noverlap = int(window_length * overlap)

        freqs, times, Sxx = spectrogram(signal, fs=fs, nperseg=nperseg, noverlap=noverlap)
        Sxx_dB = 10 * np.log10(Sxx + 1e-10)
        times_dt = df_filtered.index[0] + pd.to_timedelta(times, unit="h")

        fig_spec = go.Figure(
            data=go.Heatmap(
                z=Sxx_dB,
                x=times_dt,
                y=freqs,
                colorscale="Viridis",
                colorbar=dict(title="Power (dB)")
            )
        )
        fig_spec.update_layout(
            title=f"Spectrogram — {productiongroup.capitalize()} ({pricearea})",
            xaxis_title="Time",
            yaxis_title="Frequency (cycles/hour)",
            template="plotly_white"
        )
        st.plotly_chart(fig_spec, use_container_width=True)
