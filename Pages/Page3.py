import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv("open-meteo-subset.csv")

# Ensure time column is datetime
df['time'] = pd.to_datetime(df['time'])
df['month'] = df['time'].dt.to_period('M').astype(str)

st.title("Weather Data Explorer")

# --- Checkbox selector ---
columns = list(df.columns.drop(['time', 'month']))

st.write("Select columns to plot:")
selected_cols = []
for col in columns:
    if st.checkbox(col, value=(col == columns[0])):  # first column checked by default
        selected_cols.append(col)

# --- Month selector ---
months = sorted(df['month'].unique())
month_choice = st.select_slider(
    "Select month:",
    options=months,
    value=months[0]
)

# --- Filter data ---
df_filtered = df[df['month'] == month_choice]

# --- Plotly chart ---
if selected_cols:
    fig = px.line(
        df_filtered,
        x="time",
        y=selected_cols,
        title=f"Weather data - {month_choice}",
        labels={"value": "Value", "time": "Time", "variable": "Parameter"}
    )
    fig.update_layout(xaxis_title="Time", yaxis_title="Value")

    st.plotly_chart(fig, use_container_width=True)
