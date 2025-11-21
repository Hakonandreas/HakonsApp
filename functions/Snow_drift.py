#!/usr/bin/env python3
"""
Snow drift calculations and wind rose plotting (Tabler, 2003) made callable.

Exports:
- calculate_snow_drift(lat, lon, start_date, end_date) -> float (Qt in kg/m)
- plot_wind_rose(lat, lon, start_year, end_year) -> matplotlib.figure.Figure

Behavior:
- Attempts to load a local CSV containing hourly meteorology for the selected
  coordinates. File naming convention is assumed to be:
    open-meteo-<lat>N<lon>E<elevation>m.csv
  located under a 'data' directory next to the repository root.
- If no matching file is found, functions raise a FileNotFoundError with a
  clear message so the calling page can fail gracefully.

Assumptions:
- CSV has two header sections; the actual header starts on the 4th row.
- Columns include:
    'time'
    'temperature_2m (°C)'
    'precipitation (mm)'
    'wind_speed_10m (m/s)'
    'wind_direction_10m (°)'
- A “season” is July 1 (year Y) to June 30 (year Y+1).
"""

import re
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------------
# Core Tabler (2003) components
# ------------------------------

def compute_Qupot(hourly_wind_speeds, dt=3600):
    """Potential wind-driven transport (Qupot) [kg/m] via u^3.8."""
    total = sum((u ** 3.8) * dt for u in hourly_wind_speeds) / 233847
    return total

def sector_index(direction):
    """Map wind direction (deg) to 16-sector index."""
    return int(((direction + 11.25) % 360) // 22.5)

def compute_sector_transport(hourly_wind_speeds, hourly_wind_dirs, dt=3600):
    """Cumulative transport per 16 wind sectors (kg/m)."""
    sectors = [0.0] * 16
    for u, d in zip(hourly_wind_speeds, hourly_wind_dirs):
        idx = sector_index(d)
        sectors[idx] += ((u ** 3.8) * dt) / 233847
    return sectors

def compute_snow_transport(T, F, theta, Swe, hourly_wind_speeds, dt=3600):
    """Tabler components with controlling transport and annual Qt."""
    Qupot = compute_Qupot(hourly_wind_speeds, dt)
    Qspot = 0.5 * T * Swe
    Srwe = theta * Swe

    if Qupot > Qspot:
        Qinf = 0.5 * T * Srwe
        control = "Snowfall controlled"
    else:
        Qinf = Qupot
        control = "Wind controlled"

    Qt = Qinf * (1 - 0.14 ** (F / T))
    return {"Qupot (kg/m)": Qupot, "Qspot (kg/m)": Qspot, "Srwe (mm)": Srwe,
            "Qinf (kg/m)": Qinf, "Qt (kg/m)": Qt, "Control": control}

def compute_average_sector(df):
    """Mean sector contributions (16 values) across provided data."""
    sectors_list = []
    for s, group in df.groupby('season'):
        group = group.copy()
        group['Swe_hourly'] = group.apply(
            lambda row: row['precipitation (mm)'] if row['temperature_2m (°C)'] < 1 else 0, axis=1)
        ws = group["wind_speed_10m (m/s)"].tolist()
        wdir = group["wind_direction_10m (°)"].tolist()
        sectors = compute_sector_transport(ws, wdir)
        sectors_list.append(sectors)

    if not sectors_list:
        return np.zeros(16, dtype=float)

    avg_sectors = np.mean(sectors_list, axis=0)
    return avg_sectors

def plot_rose(avg_sector_values, overall_avg):
    """Polar wind rose for average sector values; returns Figure."""
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    num_sectors = 16
    angles = np.deg2rad(np.arange(0, 360, 360/num_sectors))

    avg_sector_values_tonnes = np.array(avg_sector_values) / 1000.0
    ax.bar(angles, avg_sector_values_tonnes, width=np.deg2rad(360/num_sectors),
           align='center', edgecolor='black')

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ax.set_xticks(angles)
    ax.set_xticklabels(directions)

    overall_tonnes = overall_avg / 1000.0
    ax.set_title(
        f"Average directional distribution of snow transport\nOverall average Qt: {overall_tonnes:,.1f} tonnes/m",
        va='bottom'
    )
    plt.tight_layout()
    return fig

def compute_fence_height(Qt, fence_type):
    """Fence height H (m) for storage capacity by fence type."""
    Qt_tonnes = Qt / 1000.0
    ft = fence_type.lower()
    if ft == "wyoming":
        factor = 8.5
    elif ft in ["slat-and-wire", "slat and wire"]:
        factor = 7.7
    elif ft == "solid":
        factor = 2.9
    else:
        raise ValueError("Unsupported fence type. Choose 'Wyoming', 'Slat-and-wire', or 'Solid'.")
    H = (Qt_tonnes / factor) ** (1 / 2.2)
    return H

# ------------------------------
# Data loading helpers
# ------------------------------

_COORD_FILE_REGEX = re.compile(
    r"open-meteo-(?P<lat>[-+]?\d+(?:\.\d+)?)N(?P<lon>[-+]?\d+(?:\.\d+)?)E(?P<elev>\d+)m\.csv$"
)

def _resolve_csv_path(lat, lon, base_dir: Path) -> Path | None:
    """
    Find the best-matching open-meteo CSV under base_dir for given lat/lon.
    The filename convention is: open-meteo-<lat>N<lon>E<elev>m.csv

    Picks the closest lat/lon embedded in filename. Returns None if not found.
    """
    candidates = []
    for p in glob.glob(str(base_dir / "open-meteo-*.csv")):
        m = _COORD_FILE_REGEX.search(Path(p).name)
        if not m:
            continue
        flat = float(m.group("lat"))
        flon = float(m.group("lon"))
        dist = abs(flat - lat) + abs(flon - lon)
        candidates.append((dist, Path(p)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def _load_meteo_csv(path: Path) -> pd.DataFrame:
    """Load CSV (skip first 3 rows), parse time, and add season column."""
    df = pd.read_csv(path, skiprows=3)
    if "time" not in df.columns:
        raise ValueError(f"CSV at {path} missing 'time' column after skiprows=3.")
    df["time"] = pd.to_datetime(df["time"])
    df["season"] = df["time"].apply(lambda dt: dt.year if dt.month >= 7 else dt.year - 1)
    return df

def _filter_range(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """Filter dataframe between start_date and end_date inclusive."""
    return df[(df["time"] >= start_date) & (df["time"] <= end_date)].copy()

# ------------------------------
# Public API
# ------------------------------

def calculate_snow_drift(lat: float, lon: float, start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """
    Calculate mean annual snow transport Qt (kg/m) over the provided date range.
    The date range should represent one seasonal year (July 1 to June 30).

    Returns Qt in kg/m (float). Raises FileNotFoundError if no CSV found.
    """
    base_dir = Path(__file__).parent.parent / "data"
    csv_path = _resolve_csv_path(lat, lon, base_dir)
    if csv_path is None:
        raise FileNotFoundError(
            f"No meteorological CSV found in {base_dir}. "
            "Expected files like 'open-meteo-<lat>N<lon>E<elev>m.csv'."
        )

    df = _load_meteo_csv(csv_path)
    df_period = _filter_range(df, pd.Timestamp(start_date), pd.Timestamp(end_date))
    if df_period.empty:
        return float("nan")

    # Hourly Swe: precip when temp < +1°C
    df_period["Swe_hourly"] = df_period.apply(
        lambda row: row["precipitation (mm)"] if row["temperature_2m (°C)"] < 1 else 0, axis=1
    )
    Swe_total = df_period["Swe_hourly"].sum()
    wind_speeds = df_period["wind_speed_10m (m/s)"].tolist()

    # Tabler parameters (adjust if needed)
    T = 3000     # m
    F = 30000    # m
    theta = 0.5  # relocation coefficient

    res = compute_snow_transport(T, F, theta, Swe_total, wind_speeds)
    return float(res["Qt (kg/m)"])

def plot_wind_rose(lat: float, lon: float, start_year: int, end_year: int):
    """
    Build a wind rose figure for the selected seasonal year range [start_year, end_year].
    Seasons are July 1 (year Y) to June 30 (year Y+1).

    Returns a matplotlib Figure. Raises FileNotFoundError if no CSV found.
    """
    base_dir = Path(__file__).parent.parent / "data"
    csv_path = _resolve_csv_path(lat, lon, base_dir)
    if csv_path is None:
        raise FileNotFoundError(
            f"No meteorological CSV found in {base_dir}. "
            "Expected files like 'open-meteo-<lat>N<lon>E<elev>m.csv'."
        )

    df = _load_meteo_csv(csv_path)
    # Filter to the selected seasons
    mask = (df["season"] >= start_year) & (df["season"] <= end_year)
    df_sel = df.loc[mask].copy()
    if df_sel.empty:
        # Return an empty figure with a clear message to avoid crashing the UI
        fig = plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "No data in selected year range", ha="center", va="center")
        plt.axis("off")
        return fig

    # Compute overall average Qt across selected seasons
    seasons = sorted(df_sel["season"].unique())
    qt_vals = []
    for s in seasons:
        start_date = pd.Timestamp(year=s, month=7, day=1)
        end_date = pd.Timestamp(year=s+1, month=6, day=30, hour=23, minute=59, second=59)
        df_season = _filter_range(df_sel, start_date, end_date)
        df_season["Swe_hourly"] = df_season.apply(
            lambda row: row["precipitation (mm)"] if row["temperature_2m (°C)"] < 1 else 0, axis=1
        )
        Swe_total = df_season["Swe_hourly"].sum()
        wind_speeds = df_season["wind_speed_10m (m/s)"].tolist()
        T, F, theta = 3000, 30000, 0.5
        res = compute_snow_transport(T, F, theta, Swe_total, wind_speeds)
        qt_vals.append(res["Qt (kg/m)"])

    overall_avg = float(np.nanmean(qt_vals)) if qt_vals else 0.0
    avg_sectors = compute_average_sector(df_sel)

    fig = plot_rose(avg_sectors, overall_avg)
    return fig
