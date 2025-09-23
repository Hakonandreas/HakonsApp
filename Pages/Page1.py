import streamlit as st
import pandas as pd


# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Data med radvise linjediagrammer")
import pandas as pd
import streamlit as st

# Import data
df = pd.read_csv("/workspaces/HakonsApp/open-meteo-subset.csv")

# Vis importerte data
st.subheader("Imported Data Table")
st.dataframe(df)

# ---- Hent ut første måned ----
# antar at time-kolonnen heter "time" og er på format YYYY-MM-DD HH:MM
df["time"] = pd.to_datetime(df["time"])
first_month_mask = df["time"].dt.month == df["time"].iloc[0].month
first_month_df = df.loc[first_month_mask]

# Transponer: rad = parameter, values = liste med målinger gjennom måneden
df_t = first_month_df.drop(columns=["time"]).transpose()

chart_df = pd.DataFrame({
    "Parameter": df_t.index,
    "Values": df_t.values.tolist()   # hver rad = liste over hele månedens verdier
})

st.subheader("First Month Data (Row-wise Line Chart)")

st.dataframe(
    chart_df,
    column_config={
        "Parameter": "Parameter",
        "Values": st.column_config.LineChartColumn(
            "Målinger (første måned)",
            y_min=int(df_t.min().min()),
            y_max=int(df_t.max().max()),
        ),
    },
    hide_index=True,
)

