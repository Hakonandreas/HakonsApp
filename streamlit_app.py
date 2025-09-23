import streamlit as st
import os

st.title("Project IND320")
st.write(
    "My Streamlit app for IND320"
)

import streamlit as st
import os

st.sidebar.title("Navigation")

# List of page names (must match filenames without .py)
pages = ["Home", "Page1", "Page2", "Page3", "Page4"]
choice = st.sidebar.radio("Go to", pages)

# Load selected page
if choice == "Home":
    st.write("Welcome to the Home page!")
else:
    # Dynamically run the selected page from pages folder
    with open(f"pages/{choice}.py", "r") as f:
        code = f.read()
    exec(code, globals())
