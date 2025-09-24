import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

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

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 5))

if col_choice:  # only plot if something is selected
    for col in col_choice:
        ax.plot(df_filtered['time'], df_filtered[col], label=col)
    ax.legend()

ax.set_title(f"Weather data - {month_choice}")
ax.set_xlabel("Time")
ax.set_ylabel("Value")
plt.xticks(rotation=45)

st.pyplot(fig)


