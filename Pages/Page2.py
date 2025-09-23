import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Page 2: Data Plot")

# Import data
df = pd.read_csv("open-meteo-subset.csv")


# Columns to choose from (excluding time)
columns = list(df.columns)
columns.remove("time")

# Checkbox selection (multiselect)
selected = st.multiselect("Velg kolonner å plotte", columns, default=columns)

# Format time column
df["time"] = pd.to_datetime(df["time"])

# Plot
fig, ax = plt.subplots(figsize=(10, 5))
if selected:
    for col in selected:
        ax.plot(df["time"], df[col], label=col)
    ax.set_ylabel("Verdi")
    ax.legend()
else:
    ax.set_ylabel("Verdi")
ax.set_xlabel("Tid")
ax.set_title("Plot av importerte data")
fig.tight_layout()
st.pyplot(fig)

