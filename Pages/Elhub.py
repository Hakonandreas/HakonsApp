import streamlit as st
import pandas as pd
import plotly.express as px
from functions.elhub_utils import load_elhub_data

st.title("Elhub Production Overview")

df = load_elhub_data()
st.success("✅ Elhub production data loaded successfully!")

# Split the layout into two columns
left, right = st.columns(2)

# Left column
with left:
    st.subheader("Price Area Overview")

    # Let the user select a price area
    price_areas = df["pricearea"].unique()
    chosen_area = st.radio("Select a price area:", options=sorted(price_areas))
    st.session_state["chosen_area"] = chosen_area

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


# Right column
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

    # Filter data based on selections
    filtered = df[
        (df["pricearea"] == chosen_area)
        & (df["productiongroup"].isin(selected_groups))
        & (df["month"] == selected_month)
    ]

    if not filtered.empty:
        # Aggregate daily total production by production group
        daily_prod = (
            filtered.groupby(["date", "productiongroup"], as_index=False)
            ["quantitykwh"]
            .sum()
            .rename(columns={"quantitykwh": "total_quantity"})
        )

        # Create line chart (daily production)
        fig_line = px.line(
            daily_prod,
            x="date",
            y="total_quantity",
            color="productiongroup",
            title=f"Daily Production in {chosen_area} - {selected_month}",
            markers=True,
            labels={
                "total_quantity": "Total Quantity (kWh)",
                "date": "Date",
                "productiongroup": "Production Group"
            }
        )

        # Improve x-axis formatting (like your notebook)
        fig_line.update_xaxes(tickformat="%b %d", hoverformat="%b %d")

        # Display the chart
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No data found for the selected combination.")

# Expander below the columns
with st.expander("Data Source / Notes"):
    st.markdown("""
    - **Database:** MongoDB collection `production` in `elhub_db`.
    - **Fields used:** `pricearea`, `productiongroup`, `quantitykwh`, `starttime`.
    - **Date processing:** 
        - `starttime` converted to datetime.
        - Aggregated daily (`date`) and monthly (`month`) for charts.
    - **Charts:** 
        - Left column: total production per production group in a selected price area.
        - Right column: daily production trends for selected production group(s) and month.
    """)
