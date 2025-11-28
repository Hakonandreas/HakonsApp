import streamlit as st

st.title("Project IND320")

st.sidebar.title("Navigation")

# Group pages into categories
page_groups = {
    "Overview": {
        "🏠 Home": "Home",
        "⚡ Elhub Production Overview": "Elhub Production Overview",
        "🌦️ Weather Data Explorer": "Weather Data Explorer",
    },
    "Analysis Tools": {
        "📈 STL & Spectrogram Analysis": "STL and Spectrogram Analysis",
        "🔍 Outlier & Anomaly Detection": "Outlier and Anomali Detection",
        "🌡️ SWC Meteorology & Energy": "SWC Meteorology and Energy",
    },
    "Mapping & Environment": {
        "🗺️ Energy Map & Snow Drift Explorer": "Energy Map & Snow Drift Explorer",
    },
    "Forecasting": {
        "📉 Forecasting": "Forecasting",
    }
}

# Sidebar menu with separators and labels
st.sidebar.markdown("### Overview")
overview_choice = st.sidebar.radio("", list(page_groups["Overview"].keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### Analysis Tools")
analysis_choice = st.sidebar.radio("", list(page_groups["Analysis Tools"].keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### Mapping & Environment")
mapping_choice = st.sidebar.radio("", list(page_groups["Mapping & Environment"].keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### Forecasting")
forecast_choice = st.sidebar.radio("", list(page_groups["Forecasting"].keys()))

# Determine current selection
choice = (
    overview_choice or 
    analysis_choice or 
    mapping_choice or 
    forecast_choice
)

page_file = (
    page_groups["Overview"].get(choice) or
    page_groups["Analysis Tools"].get(choice) or
    page_groups["Mapping & Environment"].get(choice) or
    page_groups["Forecasting"].get(choice)
)

# Load selected page
if choice == "Home":
    st.write("Welcome to the Home page!")
    st.write("Select a page from the sidebar, and enjoy some amazing visualizations!")

    with st.expander("## 📘 Table of Contents"):
        st.markdown(
            """        
        ### **1. ⚡ Elhub Production Overview**
        Get an at-a-glance understanding of electricity production patterns:
        - 🥧 *Distribution charts:* Compare total output across price areas  
        - 📈 *Hourly evolution:* Visualize how production groups change over time

        ---

        ### **2. 🔍 STL & Spectral Analysis**
        Break down complex time series to reveal hidden behavior:
        - 📊 *STL breakdown:* Separate long-term trend, seasonal movement, and noise  
        - 🎛️ *Spectral view:* Inspect frequency components over time

        ---

        ### **3. 🌦️ Weather Data Explorer (ERA5)**
        Interactive exploration of meteorological variables:
        - 🌡️ Choose specific variables and time windows  
        - 📉 Create time-series plots for single or multiple weather metrics

        ---

        ### **4. 🚨 Outlier & Anomaly Detection**
        Identify atypical or extreme meteorological events:
        - 🌡️ *Temperature detection:* DCT + SPC-based classification  
        - 🌧️ *Rainfall anomalies:* Discover irregularities using LOF

        ---

        ### **5. 🗺️ Energy Map & ❄️ Snow Drift Explorer**
        Interactive spatial and snow analysis:
        - 🔌 *Energy Map:* Production/consumption per NO1–NO5  
        - ❄️ *Snow Drift:* Seasonal & monthly calculations  
        - 🧭 *Wind Rose:* Snow-driven wind distribution

        ---

        ### **6. 🔄 SWC Meteorology and Energy**
        Daily sliding window correlation analysis:
        - 🔗 Compare energy & weather variables  
        - ⏱️ Apply lags to explore lead/lag behavior  
        - 📊 Visualize energy, weather & correlation series

        ---

        ### **7. 📉 Forecasting (SARIMAX)**
        Interactive forecasting tools:
        - ⚙️ Configure ARIMA + seasonal parameters  
        - 📅 Select training windows  
        - 📈 Generate forecasts with confidence intervals
            """)

else:
    # Dynamically run the selected page from Pages folder
    with open(f"Pages/{choice}.py", "r") as f:
        code = f.read()
    exec(code, globals())

# Initialize session state variable if not present
if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = "NO1" # Default area

