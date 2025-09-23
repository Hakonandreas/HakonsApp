import streamlit as st
import pandas as pd

st.title("Page 2: Data Plot")

# Import data
df = pd.read_csv("open-meteo-subset.csv")

# Columns to choose from (excluding time)
columns = list(df.columns)
columns.remove("time")
select_options = ["All columns"] + columns

# Dropdown menu
selected = st.selectbox("Choose column to plot", select_options)

# Format time column
df["time"] = pd.to_datetime(df["time"])

# Plot
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 5))
if selected == "All columns":
	for col in columns:
		ax.plot(df["time"], df[col], label=col)
	ax.set_ylabel("Value")
else:
	ax.plot(df["time"], df[selected], label=selected)
	ax.set_ylabel(selected)
ax.set_xlabel("Time")
ax.set_title("Imported Data Plot")
ax.legend()
fig.tight_layout()
st.pyplot(fig)

