import streamlit as st
'''
st.title("Project IND320")

st.sidebar.title("Navigation")

# List of page names (must match filenames without .py)
pages = ["Home", "Raw Data", "Weather Data Explorer", "Elhub", "Page4"]
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
'''

import streamlit as st

st.title("Project IND320")
st.sidebar.title("Navigation")

pages = ["Home", "Raw Data", "Weather Data Explorer", "Elhub", "Page4"]
choice = st.sidebar.selectbox("Go to", pages)

# Check secrets first
st.write("Secrets currently loaded:", st.secrets)

if choice == "Home":
    st.write("Welcome to the Home page!")
else:
    page_path = f"Pages/{choice}.py"
    st.write(f"Loading page: {page_path}")
    with open(page_path, "r") as f:
        code = f.read()
    exec(code, globals())