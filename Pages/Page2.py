import pandas as pd
import streamlit as st
import plotly.express as px

# Load data
df = pd.read_csv("open-meteo-subset.csv")

# Ensure time column is datetime
df['time'] = pd.to_datetime(df['time'])
df['month'] = df['time'].dt.to_period('M').astype(str)

st.title("Weather Data Explorer")

# --- Column selector (checkbox-style) ---
columns = list(df.columns.drop(['time', 'month']))
col_choice = st.multiselect(
    "Select columns to plot:",
    options=columns,
    default=[columns[0]]  # default: first column checked
)

# --- Month selector ---
months = sorted(df['month'].unique())
month_choice = st.select_slider(
    "Select month:",
    options=months,
    value=months[0]
)

# Filter data
df_filtered = df[df['month'] == month_choice]

# Plotting
if col_choice:  # only plot if something is selected
    fig = px.line(
        df_filtered,
        x="time",
        y=col_choice,
        title=f"Weather data - {month_choice}",
        labels={"value": "Value", "time": "Time", "variable": "Parameter"}
    )
    st.plotly_chart(fig, use_container_width=True)

