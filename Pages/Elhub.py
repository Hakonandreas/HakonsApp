import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Connect to MongoDB
uri = st.secrets["mongodb"]["uri"]
client = MongoClient(uri)
db = client.elhub_db
st.success("Successfully connected to MongoDB!")

# Load data
collection = db.production
data = list(collection.find())
df = pd.DataFrame(data)

# Convert starttime to datetime and extract useful columns
df["starttime"] = pd.to_datetime(df["starttime"])
df["month"] = df["starttime"].dt.strftime("%Y-%m")  # e.g., "2021-12"
df["date"] = df["starttime"].dt.date

# Split the layout into two columns
left, right = st.columns(2)

# LEFT COLUMN
with left:
    st.subheader("Price Area Overview")

    # Let the user select a price area
    price_areas = df["pricearea"].unique()
    chosen_area = st.radio("Select a price area:", options=sorted(price_areas))

    # Filter and aggregate like in my notebook
    area_data = (
        df[df["pricearea"] == chosen_area]
        .groupby("productiongroup", as_index=False)["quantitykwh"]
        .sum()
        .rename(columns={"quantitykwh": "total_quantity"})
    )

    # Create pie chart
    fig = px.pie(
        area_data,
        names="productiongroup",
        values="total_quantity",
        title=f"Total Production in {chosen_area} (2021)",
        hole=0.0
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


# RIGHT COLUMN
with right:
    st.subheader("Production Trends")

    # Select production group(s)
    production_groups = sorted(df["productiongroup"].unique())
    selected_groups = st.pills(
        "Select production group(s):",
        options=production_groups,
        selection_mode="multi",
        default=production_groups[:2] if len(production_groups) > 1 else production_groups
    )

    # Select month
    months = sorted(df["month"].unique())
    selected_month = st.selectbox("Select month:", options=months)

    # Filter based on all selections
    filtered = df[
        (df["pricearea"] == chosen_area)
        & (df["productiongroup"].isin(selected_groups))
        & (df["month"] == selected_month)
    ]

    # Create line chart (e.g., daily quantity within the month)
    if not filtered.empty:
        fig_line = px.line(
            filtered,
            x="date",
            y="quantitykwh",
            color="productiongroup",
            title=f"Production Trends in {chosen_area} - {selected_month}",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No data found for the selected combination.")

