#!/usr/bin/env python3
"""
Snow drift calculation and wind rose plotting for a selected year range
using functions from snow_drift.py.
"""

import pandas as pd
from functions.Snow_drift import (
    compute_yearly_results,
    compute_average_sector,
    plot_rose
)

def main():
    # ---------------- Check for coordinates ----------------
    coordinates_selected = False  # Replace with actual map selection logic
    if not coordinates_selected:
        print("No coordinates selected. Snow drift calculation cannot proceed.")
        return

    # ---------------- User input for year range ----------------
    try:
        start_year = int(input("Enter start year (YYYY): "))
        end_year = int(input("Enter end year (YYYY): "))
    except ValueError:
        print("Invalid year input.")
        return
    if end_year < start_year:
        print("End year must be greater than or equal to start year.")
        return

    # ---------------- Load CSV data ----------------
    filename = "open-meteo-60.57N7.60E1212m.csv"
    df = pd.read_csv(filename, skiprows=3)
    df['time'] = pd.to_datetime(df['time'])

    # ---------------- Snow transport parameters ----------------
    T = 3000      # Maximum transport distance (m)
    F = 30000     # Fetch distance (m)
    theta = 0.5   # Relocation coefficient

    # ---------------- Compute yearly results ----------------
    yearly_df = compute_yearly_results(df, T, F, theta, start_year, end_year)
    if yearly_df.empty:
        print("No data available for the selected year range.")
        return

    overall_avg = yearly_df['Qt (kg/m)'].mean()
    print("\nYearly average snow drift per season:")
    print(yearly_df.to_string(index=False, formatters={'Qt (kg/m)': lambda x: f"{x:.1f}"}))
    print(f"\nOverall average Qt over all seasons: {overall_avg / 1000:.1f} tonnes/m")

    # ---------------- Compute and plot wind rose ----------------
    avg_sectors = compute_average_sector(df, start_year, end_year)
    plot_rose(avg_sectors, overall_avg)


if __name__ == "__main__":
    main()
