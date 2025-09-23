import streamlit as st

st.title("Project IND320")
st.write(
    "My Streamlit app for IND320"
)

# sidebar menu with navigation to the pages
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["page1", "page2", "page3", "page4"])
if page == "page1":
    st.header("Page 1")
    st.write("This is page 1 content.")
elif page == "page2":
    st.header("Page 2")
    st.write("This is page 2 content.")
elif page == "page3":       
    st.header("Page 3")
    st.write("This is page 3 content.")
elif page == "page4":   
    st.header("Page 4")
    st.write("This is page 4 content.")


