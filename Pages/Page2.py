import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Page 2: Data Plot")

# Import data
df = pd.read_csv("open-meteo-subset.csv")

# Ensure time column is datetime
df['time'] = pd.to_datetime(df['time'])
df['month'] = df['time'].dt.to_period('M').astype(str)  # e.g. '2025-01'

st.title("Weather Data Explorer")

# --- Column selector ---
columns = list(df.columns.drop(['time', 'month']))
col_choice = st.selectbox("Select a column to plot:", ["All columns"] + columns)

# --- Month selector ---
months = sorted(df['month'].unique())
month_choice = st.select_slider(
    "Select month:",
    options=months,
    value=months[0]  # default first month
)

# Filter data
df_filtered = df[df['month'] == month_choice]

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 5))

if col_choice == "All columns":
    for col in columns:
        ax.plot(df_filtered['time'], df_filtered[col], label=col)
    ax.legend()
else:
    ax.plot(df_filtered['time'], df_filtered[col_choice], label=col_choice)
    ax.legend()

ax.set_title(f"Weather data - {month_choice}")
ax.set_xlabel("Time")
ax.set_ylabel("Value")
plt.xticks(rotation=45)

st.pyplot(fig)


