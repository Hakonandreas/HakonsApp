import streamlit as st
import pandas as pd

'''
# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Data med radvise linjediagrammer")

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

'''

import pandas as pd
import streamlit as st

# Import data
df = pd.read_csv("open-meteo-subset.csv")

# Vis importerte data
st.subheader("Imported Data Table")
st.dataframe(df)

# ---- Hent ut første måned ----
df["time"] = pd.to_datetime(df["time"])
first_month_mask = df["time"].dt.month == df["time"].iloc[0].month
first_month_df = df.loc[first_month_mask]

# Transponer: rad = parameter, values = liste med målinger gjennom måneden
df_t = first_month_df.drop(columns=["time"]).transpose()

chart_df = pd.DataFrame({
    "Parameter": df_t.index,
    "Values": df_t.values.tolist()
})

# Tilpassede y-limits for utvalgte parametere
custom_limits = {
    "precipitation": (0, first_month_df["precipitation"].max()),
    "wind_gusts_10m": (0, first_month_df["wind_gusts_10m"].max()),
    "wind_speed_10m": (0, first_month_df["wind_speed_10m"].max()),
}

# Bygg column_config dynamisk
column_config = {
    "Parameter": "Parameter",
    "Values": st.column_config.LineChartColumn(
        "Målinger (første måned)",
        y_min=int(df_t.min().min()),   # fallback for alle andre
        y_max=int(df_t.max().max()),
    )
}

# Lag dataframe-visning
st.subheader("First Month Data (Row-wise Line Chart)")

st.dataframe(
    chart_df,
    column_config=column_config,
    hide_index=True,
)

# ---- Ekstra: lag en variant med custom y-limits ----
chart_df_custom = chart_df.copy()

# Vi må lage column_config per rad hvis vi vil vise spesifikke skalaer
# Derfor splitter vi opp tabellen i to deler: med/uten custom limits
st.subheader("First Month Data (with custom y-limits on selected parameters)")

rows = []
for i, row in chart_df.iterrows():
    param = row["Parameter"]
    values = row["Values"]

    if param in custom_limits:
        ymin, ymax = custom_limits[param]
    else:
        ymin, ymax = int(df_t.min().min()), int(df_t.max().max())

    # Lag minitabell for hver parameter
    st.dataframe(
        pd.DataFrame({"Parameter": [param], "Values": [values]}),
        column_config={
            "Parameter": "Parameter",
            "Values": st.column_config.LineChartColumn(
                f"{param} (first month)", y_min=ymin, y_max=ymax
            ),
        },
        hide_index=True,
    )
