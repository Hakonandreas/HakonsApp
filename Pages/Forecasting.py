import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

# Import your Elhub loaders
from functions.elhub_utils import load_elhub_data, load_elhub_consumption

# --- Helpers ---
def list_target_columns(df: pd.DataFrame) -> list:
    return list(df.columns)

def split_train_test(df: pd.DataFrame, target_col: str, train_end: str):
    y_train = df[target_col].loc[:train_end]
    y_full = df[target_col]
    return y_train, y_full

def fit_sarimax(y, exog, order, seasonal_order, trend):
    mod = sm.tsa.statespace.SARIMAX(
        endog=y,
        exog=exog,
        order=order,
        seasonal_order=seasonal_order,
        trend=trend,
        enforce_stationarity=True,
        enforce_invertibility=True,
    )
    res = mod.fit(disp=False)
    return mod, res

def refit_and_filter_full(y_full, exog_full, params, order, seasonal_order, trend):
    mod_full = sm.tsa.statespace.SARIMAX(
        endog=y_full,
        exog=exog_full,
        order=order,
        seasonal_order=seasonal_order,
        trend=trend,
        enforce_stationarity=True,
        enforce_invertibility=True,
    )
    res_full = mod_full.filter(params)
    return mod_full, res_full

def make_predictions(res, dynamic_start, start=None, end=None):
    predict = res.get_prediction(start=start, end=end)
    predict_ci = predict.conf_int()

    predict_dy = res.get_prediction(dynamic=dynamic_start, start=start, end=end)
    predict_dy_ci = predict_dy.conf_int()

    return {
        "one_step_mean": predict.predicted_mean,
        "one_step_ci": predict_ci,
        "dynamic_mean": predict_dy.predicted_mean,
        "dynamic_ci": predict_dy_ci,
    }

# --- Streamlit UI ---
st.title("SARIMAX Forecasting of Energy Production/Consumption")

# Load Elhub data
df = load_elhub_data()  # or load_elhub_consumption() depending on your dataset

# Sidebar: target and exogenous selection
target_col = st.sidebar.selectbox("Target", options=list_target_columns(df))
exog_options = [c for c in df.columns if c != target_col]
exog_cols = st.sidebar.multiselect("Exogenous variables", options=exog_options)

# Sidebar: timeframe
train_end = st.sidebar.text_input("Training end date", value=str(df.index[int(len(df)*0.7)])[:10])
dynamic_start = st.sidebar.text_input("Dynamic forecast start date", value=train_end)

# Sidebar: SARIMAX parameters
p = st.sidebar.number_input("p", 0, 5, 1)
d = st.sidebar.number_input("d", 0, 2, 1)
q = st.sidebar.number_input("q", 0, 5, 1)
P = st.sidebar.number_input("P (seasonal)", 0, 5, 1)
D = st.sidebar.number_input("D (seasonal)", 0, 2, 1)
Q = st.sidebar.number_input("Q (seasonal)", 0, 5, 1)
m = st.sidebar.number_input("Seasonal period (m)", 1, 365, 12)
trend = st.sidebar.selectbox("Trend", options=[None, 'n', 'c', 't', 'ct'], index=2)

# --- Train and fit ---
y_train, y_full = split_train_test(df, target_col, train_end)
exog_train = df[exog_cols].loc[:train_end] if exog_cols else None
exog_full = df[exog_cols] if exog_cols else None

mod_train, res_train = fit_sarimax(y_train, exog_train, (p,d,q), (P,D,Q,m), trend)
mod_full, res_full = refit_and_filter_full(y_full, exog_full, res_train.params, (p,d,q), (P,D,Q,m), trend)

# --- Predictions ---
preds = make_predictions(res_full, dynamic_start=pd.to_datetime(dynamic_start), start=train_end)

# --- Plot ---
fig, ax = plt.subplots(figsize=(12,5))
df[target_col].plot(ax=ax, style='o', label='Observed')

preds["one_step_mean"].plot(ax=ax, style='r--', label='One-step-ahead')
ci1 = preds["one_step_ci"]
ax.fill_between(ci1.index, ci1.iloc[:,0], ci1.iloc[:,1], color='r', alpha=0.15)

preds["dynamic_mean"].plot(ax=ax, style='g', label=f'Dynamic (from {dynamic_start})')
ci2 = preds["dynamic_ci"]
ax.fill_between(ci2.index, ci2.iloc[:,0], ci2.iloc[:,1], color='g', alpha=0.15)

ax.set_title(f"{target_col} forecast")
ax.set_xlabel("Date")
ax.set_ylabel(target_col)
ax.legend()
st.pyplot(fig)

# --- Diagnostics ---
st.subheader("Model summary")
st.text(res_train.summary().as_text())
