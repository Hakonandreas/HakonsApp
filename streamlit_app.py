import streamlit as st

st.title("Project IND320")

st.sidebar.title("Navigation")

# List of page names (must match filenames without .py)
pages = ["Home", "Elhub", "STL and Spectrogram Analysis", 
         "Raw Data", "Weather Data Explorer", "Outlier and Anomali Detection", 
         "Map", "Snowdrift", "Meteorology and Energy production"]
choice = st.sidebar.selectbox("Go to", pages)

# Load selected page
if choice == "Home":
    st.write("Welcome to the Home page!")
    st.write("Select a page from the sidebar, and enjoy some amazing visualizations!")
else:
    # Dynamically run the selected page from Pages folder
    with open(f"Pages/{choice}.py", "r") as f:
        code = f.read()
    exec(code, globals())

# Initialize session state variable if not present
if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = "NO1" # Default area

