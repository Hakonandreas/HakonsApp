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

st.set_page_config(
    page_title="Project IND320",
    page_icon="📊" # You can use an emoji here
)

st.title("Welcome to Project IND320!")
st.sidebar.success("Select a page above.")

st.write("Select a page from the sidebar to enjoy some amazing visualizations!")