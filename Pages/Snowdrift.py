#!/usr/bin/env python3
"""
Snow drift calculation and interactive wind rose plotting using Plotly
for a selected year range and coordinates.
"""

import pandas as pd
import plotly.graph_objects as go
from functions.Snow_drift import compute_yearly_results, compute_average_sector

# ---------------- Plotly wind rose ----------------
def plot_rose_plotly(avg_sector_values, overall_avg):
    """
    Create an interactive 16-sector wind rose using Plotly.
    
    Parameters:
        avg_sector_values: list or array of 16 average snow transport values (kg/m)
        overall_avg: overall average Qt (kg/m) across selected years
    """
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    avg_tonnes = [v/1000.0 for v in avg_sector_values]  # convert to tonnes/m

    fig = go.Figure(go.Barpolar(
        r=avg_tonnes,
        theta=directions,
        width=[22.5]*16,
        marker_color='skyblue',
        marker_line_color='black',
        marker_line_width=1,
        opacity=0.8
    ))

    fig.update_layout(
        title=f'Average Directional Snow Transport<br>Overall Qt: {overall_avg/1000:.1f} tonnes/m',
        polar=dict(
            radialaxis=dict(title='Snow Transport (tonnes/m)', angle=90, tickangle=90),
            angularaxis=dict(direction='clockwise', rotation=90)
        ),
        showlegend=False
    )
    fig.show()


# ---------------- Main function ----------------
def main():
    # Check if coordinates are selected
    coordinates_selected = False  # <-- replace with actual map selection logic
    if not coordinates_selected:
        print("No coordinates selected. Snow drift calculation cannot proceed.")
        return

    # User input for year range
    try:
        start_year = int(input("Enter start year (YYYY): "))
        end_year = int(input("Enter end year (YYYY): "))
    except ValueError:
        print("Invalid year input.")
        return
    if end_year < start_year:
        print("End year must be >= start year.")
        return

    # Load CSV data
    filename = "open-meteo-60.57N7.60E1212m.csv"
    df = pd.read_csv(filename, skiprows=3)
    df['time'] = pd.to_datetime(df['time'])

    # Snow transport parameters
    T = 3000
    F = 30000
    theta = 0.5

    # Compute yearly results
    yearly_df = compute_yearly_results(df, T, F, theta, start_year, end_year)
    if yearly_df.empty:
        print("No data available for the selected year range.")
        return

    overall_avg = yearly_df['Qt (kg/m)'].mean()
    print("\nYearly average snow drift per season:")
    print(yearly_df.to_string(index=False, formatters={'Qt (kg/m)': lambda x: f"{x:.1f}"}))
    print(f"\nOverall average Qt over all seasons: {overall_avg / 1000:.1f} tonnes/m")

    # Compute average sector values and plot wind rose with Plotly
    avg_sectors = compute_average_sector(df, start_year, end_year)
    plot_rose_plotly(avg_sectors, overall_avg)


if __name__ == "__main__":
    main()
