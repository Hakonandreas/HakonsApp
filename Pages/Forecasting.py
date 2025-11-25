import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from functions.elhub_utils import load_elhub_data, load_elhub_consumption

# =========================================================
# Helper: Clean exogenous variables
# =========================================================
def sanitize_exog(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return None
    df = df.copy()

    # Remove datetime columns
    for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
        df.drop(columns=col, inplace=True)

    # One-hot encode categorical
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if len(cat_cols) > 0:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    # Convert booleans
    bool_cols = df.select_dtypes(include=["bool"]).columns
    df[bool_cols] = df[bool_cols].astype(int)

    # Convert everything to numeric, drop non-convertible columns
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1)

    return df

# =========================================================
# Helper: Prepare series (daily resampling + grouping)
# =========================================================
def prepare_series(df: pd.DataFrame, target="quantitykwh"):
    """Returns a dict with grouped daily series options."""
    if df.empty:
        return {}

    group_cols = [c for c in ["productiongroup", "consumptiongroup"] if c in df.columns]
    pa_col = "pricearea" if "pricearea" in df.columns else None

    results = {}

    for group_col in group_cols:
        groups = df[group_col].dropna().unique()
        for g in groups:

            subset = df[df[group_col] == g].copy()

            if pa_col:
                priceareas = subset[pa_col].dropna().unique()
            else:
                priceareas = ["ALL"]

            for pa in priceareas:
                if pa_col and pa != "ALL":
                    sub = subset[subset[pa_col] == pa]
                else:
                    sub = subset

                if sub.empty:
                    continue

                # --- Aggregate to daily ---
                s = (
                    sub.groupby("starttime")[target]
                    .sum()
                    .resample("D")
                    .sum()
                    .fillna(0)
                )

                # Try setting a frequency
                try:
                    freq = s.index.inferred_freq
                    if freq:
                        s = s.asfreq(freq)
                except:
                    pass

                results[(group_col, g, pa)] = s

    return results


# =========================================================
# SARIMAX fitting
# =========================================================
@st.cache_resource
def fit_sarimax(y, exog, order, seasonal_order):
    model = sm.tsa.SARIMAX(
        y,
        exog=exog,
        order=order,
        seasonal_order=seasonal_order,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    res = model.fit(disp=False)
    return model, res


# =========================================================
# Streamlit UI
# =========================================================
st.set_page_config(page_title="Energy Forecasting", layout="wide")
st.title("🔮 SARIMAX Forecasting of Energy Production / Consumption")

# -----------------------------
# Dataset selection
# -----------------------------
dataset_choice = st.sidebar.radio("Select dataset", ["Consumption", "Production"])
df_raw = load_elhub_consumption() if dataset_choice == "Consumption" else load_elhub_data()

# Standardize timestamp column
df_raw["starttime"] = pd.to_datetime(df_raw["starttime"])
df_raw.set_index("starttime", inplace=True)

# Prepare grouped daily series
series_dict = prepare_series(df_raw)

if not series_dict:
    st.error("No valid time series found in database.")
    st.stop()

# -----------------------------
# Series selection
# -----------------------------
selection_keys = {
    f"{key[0]} = {key[1]} | pricearea = {key[2]}": key for key in series_dict.keys()
}
chosen_label = st.selectbox("Choose time series:", list(selection_keys.keys()))
chosen_key = selection_keys[chosen_label]
series = series_dict[chosen_key]

st.line_chart(series, height=250)

# -----------------------------
# Training period
# -----------------------------
st.header("Training Period")

min_date = series.index.min().date()
max_date = series.index.max().date()

train_start, train_end = st.date_input(
    "Select training period:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

train_start_dt = pd.Timestamp(train_start)
train_end_dt = pd.Timestamp(train_end)

y_train = series.loc[train_start_dt:train_end_dt]

# ----------------------------------
# Exogenous variable selection
# ----------------------------------
st.sidebar.header("Exogenous Variables")
exog_cols = [c for c in df_raw.columns if c not in ["quantitykwh", "productiongroup", "consumptiongroup"]]
exog_selected = st.sidebar.multiselect("Select exogenous variables (optional)", exog_cols)

if exog_selected:
    exog_raw = df_raw[exog_selected].resample("D").mean().fillna(method="ffill")
    exog_train = sanitize_exog(exog_raw.loc[y_train.index])
else:
    exog_train = None

# --------------------------------------
# SARIMAX param input
# --------------------------------------
st.sidebar.header("SARIMAX Parameters")
p = st.sidebar.number_input("p (AR)", 0, 5, 1)
d = st.sidebar.number_input("d (diff)", 0, 2, 1)
q = st.sidebar.number_input("q (MA)", 0, 5, 1)

P = st.sidebar.number_input("P (seasonal AR)", 0, 2, 0)
D = st.sidebar.number_input("D (seasonal diff)", 0, 1, 0)
Q = st.sidebar.number_input("Q (seasonal MA)", 0, 2, 0)
m = st.sidebar.number_input("m (season period)", 1, 365, 7)

forecast_steps = st.sidebar.number_input("Forecast horizon (days)", 1, 365, 30)

run = st.sidebar.button("Run Forecast")

# =========================================================
# Forecast
# =========================================================
if run:
    with st.spinner("Fitting SARIMAX model..."):
        model, res = fit_sarimax(
            y=y_train,
            exog=exog_train,
            order=(p, d, q),
            seasonal_order=(P, D, Q, m),
        )

    forecast = res.get_forecast(steps=forecast_steps)
    mean = forecast.predicted_mean
    ci = forecast.conf_int()

    # Plot ----------------------------------
    st.header("📈 Forecast")
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(y_train.index, y_train.values, label="Observed")
    ax.plot(mean.index, mean.values, label="Forecast", color="red")

    ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], alpha=0.2, color="red")

    ax.set_title(f"Forecast ({dataset_choice})")
    ax.legend()

    st.pyplot(fig)

    st.subheader("Model Summary")
    st.text(res.summary().as_text())
