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
    dt_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns
    df = df.drop(columns=dt_cols)

    # One-hot encode categorical variables
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    if len(cat_cols) > 0:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    # Convert boolean to int
    bool_cols = df.select_dtypes(include=["bool"]).columns
    if len(bool_cols) > 0:
        df[bool_cols] = df[bool_cols].astype(int)

    # Convert all to numeric, drop non-convertible
    df = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="any")

    return df


# =========================================================
# Helper: Prepare grouped time series (daily)
# =========================================================
def prepare_series(df: pd.DataFrame, target="quantitykwh"):
    """Returns a dict of: (group, pricearea) -> daily series."""
    results = {}

    # Depending on dataset selection, only one of these exists
    group_col = "consumptiongroup" if "consumptiongroup" in df.columns else "productiongroup"

    for group in sorted(df[group_col].dropna().unique()):
        sub = df[df[group_col] == group]

        for pa in sorted(sub["pricearea"].dropna().unique()):
            pa_sub = sub[sub["pricearea"] == pa]

            if pa_sub.empty:
                continue

            daily = (
                pa_sub[target]
                .groupby(pa_sub.index)
                .sum()
                .resample("D")
                .sum()
                .fillna(0)
            )

            # Try set frequency for SARIMAX
            try:
                freq = daily.index.inferred_freq
                if freq:
                    daily = daily.asfreq(freq)
            except Exception:
                pass

            results[(group, pa)] = daily

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
        enforce_invertibility=False,
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

df_raw["starttime"] = pd.to_datetime(df_raw["starttime"])
df_raw = df_raw.set_index("starttime")

series_dict = prepare_series(df_raw)

if not series_dict:
    st.error("No valid time series found.")
    st.stop()


# =========================================================
# Time series selection (similar to the alternative)
# =========================================================
st.header("Select Time Series")

group_col = "consumptiongroup" if dataset_choice == "Consumption" else "productiongroup"

# Group dropdown
groups = sorted(df_raw[group_col].dropna().unique())
selected_group = st.selectbox("Group:", groups)

# Price area dropdown
priceareas = sorted(df_raw[df_raw[group_col] == selected_group]["pricearea"].dropna().unique())
selected_pa = st.selectbox("Price Area:", priceareas)

chosen_key = (selected_group, selected_pa)
series = series_dict[chosen_key]

st.line_chart(series, height=240)


# =========================================================
# Training period selection
# =========================================================
st.header("Training Period")
min_date = series.index.min().date()
max_date = series.index.max().date()

train_start, train_end = st.date_input(
    "Select training period:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

train_start = pd.Timestamp(train_start)
train_end = pd.Timestamp(train_end)
y_train = series.loc[train_start:train_end]


# =========================================================
# SARIMAX parameters
# =========================================================
st.sidebar.header("SARIMAX Parameters")

# Non-seasonal parameters
p = st.sidebar.number_input("p (AR)", 1, 5, 1)   # min 1, default 1
d = st.sidebar.number_input("d (diff)", 0, 2, 1) # allow 0, default 1
q = st.sidebar.number_input("q (MA)", 1, 5, 1)   # min 1, default 1

# Seasonal parameters
P = st.sidebar.number_input("P (seasonal AR)", 0, 2, 1)  # allow 0, default 1
D = st.sidebar.number_input("D (seasonal diff)", 0, 1, 0) # allow 0, default 0
Q = st.sidebar.number_input("Q (seasonal MA)", 0, 2, 1)  # allow 0, default 1
m = st.sidebar.number_input("m (seasonality)", 1, 365, 7) # min 1, default 7

# Forecast horizon
forecast_steps = st.sidebar.number_input("Forecast horizon (days)", 1, 365, 30)

run = st.sidebar.button("Run Forecast")



# =========================================================
# Forecasting
# =========================================================
if run:
    with st.spinner("Fitting SARIMAX model…"):
        model, res = fit_sarimax(
            y=y_train,
            exog=None,
            order=(p, d, q),
            seasonal_order=(P, D, Q, m),
        )

    forecast = res.get_forecast(steps=forecast_steps)
    mean = forecast.predicted_mean
    ci = forecast.conf_int()

    st.header("📈 Forecast")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(y_train.index, y_train.values, label="Observed")
    ax.plot(mean.index, mean.values, label="Forecast")
    ax.fill_between(ci.index, ci.iloc[:, 0], ci.iloc[:, 1], alpha=0.2)

    ax.legend()
    st.pyplot(fig)

    st.subheader("Model Summary")
    st.text(res.summary().as_text())

# =========================================================
# Explanation of Parameters
# =========================================================
with st.expandeer("ℹ️ Parameter Explanations"):

    st.markdown("""
    **Non-seasonal parameters (ARIMA):**
    - **p (AR)**: Autoregressive order. Number of past values used to predict the current value.
    - **d (diff)**: Differencing order. Number of times the series is differenced to remove trends and make it stationary.
    - **q (MA)**: Moving average order. Number of past forecast errors included in the model.

    **Seasonal parameters (SARIMA):**
    - **P (seasonal AR)**: Seasonal autoregressive order. Like `p`, but applied to seasonal lags.
    - **D (seasonal diff)**: Seasonal differencing order. Number of seasonal differences applied (e.g., yearly or weekly).
    - **Q (seasonal MA)**: Seasonal moving average order. Like `q`, but applied to seasonal lags.
    - **m (seasonality)**: Length of the seasonal cycle (e.g., 7 for weekly seasonality in daily data, 365 for yearly).

    **Forecast settings:**
    - **Forecast horizon (days)**: How many future steps (days) to forecast.
    """)
