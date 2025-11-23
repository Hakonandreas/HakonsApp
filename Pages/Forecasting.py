import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from functions.elhub_utils import load_elhub_data, load_elhub_consumption

# --- Helper functions ---
def sanitize_exog(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()

    # Drop datetime columns
    for col in df_clean.select_dtypes(include=['datetime', 'datetimetz']).columns:
        df_clean.drop(columns=col, inplace=True)

    # Encode categorical columns
    for col in df_clean.select_dtypes(include=['object', 'category']).columns:
        df_clean = pd.get_dummies(df_clean, columns=[col], drop_first=True)

    # Convert booleans to integers
    for col in df_clean.select_dtypes(include=['bool']).columns:
        df_clean[col] = df_clean[col].astype(int)

    # Ensure all numeric
    df_clean = df_clean.apply(pd.to_numeric, errors='coerce').dropna(axis=1)

    return df_clean

@st.cache_data
def get_data(dataset_choice):
    if dataset_choice == "Consumption":
        df = load_elhub_consumption()
    else:
        df = load_elhub_data()
    # Ensure datetime index
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    elif 'starttime' in df.columns:
        df['starttime'] = pd.to_datetime(df['starttime'])
        df.set_index('starttime', inplace=True)
    return df

@st.cache_resource
def fit_sarimax(y, exog, order, seasonal_order):
    mod = sm.tsa.statespace.SARIMAX(
        endog=y,
        exog=exog,
        order=order,
        seasonal_order=seasonal_order,
        trend='c',
        enforce_stationarity=True,
        enforce_invertibility=True,
    )
    res = mod.fit(disp=False)
    return mod, res

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
st.set_page_config(page_title="Energy Forecasting", layout="wide")
st.title("🔮 SARIMAX Forecasting of Energy Consumption or Production")

# Dataset selector
dataset_choice = st.sidebar.radio("Select dataset", ["Consumption", "Production"])
df = get_data(dataset_choice)

# Fixed target
target_col = "quantitykwh"

# Sidebar: exogenous variable selection
exog_options = [col for col in df.columns if col not in [target_col, "_id", "date", "starttime"]]
exog_cols = st.sidebar.multiselect("Select exogenous variables (optional)", options=exog_options)

# Sidebar: timeframe
st.sidebar.header("Timeframe")
default_date = df.index[int(len(df)*0.7)].date()
train_end = st.sidebar.date_input("Training end date", value=default_date)
dynamic_start = st.sidebar.date_input("Dynamic forecast start date", value=default_date)

# Sidebar: simplified SARIMAX parameters
st.sidebar.header("SARIMAX Parameters")
p = st.sidebar.number_input("AR order (p)", 0, 5, 1)
d = st.sidebar.number_input("Differencing (d)", 0, 2, 1)
q = st.sidebar.number_input("MA order (q)", 0, 5, 1)
P = st.sidebar.number_input("Seasonal AR (P)", 0, 5, 1)
Q = st.sidebar.number_input("Seasonal MA (Q)", 0, 5, 1)
m = st.sidebar.number_input("Seasonal period (m)", 1, 365, 12)

# --- Prepare data ---
train_end_ts = pd.to_datetime(train_end)
dynamic_start_ts = pd.to_datetime(dynamic_start)

y_train = df[target_col].loc[:train_end_ts]
exog_train = sanitize_exog(df[exog_cols].loc[:train_end_ts]) if exog_cols else None

# --- Fit model ---
mod_train, res_train = fit_sarimax(y_train, exog_train, (p,d,q), (P,1,Q,m))

# --- Predictions ---
preds = make_predictions(res_train, dynamic_start=dynamic_start_ts, start=train_end_ts)

# --- Plot ---
st.header("📈 Forecast Plot")
fig, ax = plt.subplots(figsize=(12,5))

# Downsample for speed if dataset is huge
df[target_col].iloc[::10].plot(ax=ax, style='o', label='Observed', markersize=2)

preds["one_step_mean"].plot(ax=ax, style='r--', label='One-step-ahead')
ci1 = preds["one_step_ci"]
ax.fill_between(ci1.index, ci1.iloc[:,0], ci1.iloc[:,1], color='r', alpha=0.15)

preds["dynamic_mean"].plot(ax=ax, style='g', label=f'Dynamic (from {dynamic_start})')
ci2 = preds["dynamic_ci"]
ax.fill_between(ci2.index, ci2.iloc[:,0], ci2.iloc[:,1], color='g', alpha=0.15)

ax.set_title(f"{target_col} forecast — {dataset_choice}")
ax.set_xlabel("Date")
ax.set_ylabel("kWh")
ax.legend()
st.pyplot(fig)

# --- Diagnostics ---
st.header("🧪 Model Diagnostics")
st.subheader("SARIMAX Summary")
st.text(res_train.summary().as_text())
