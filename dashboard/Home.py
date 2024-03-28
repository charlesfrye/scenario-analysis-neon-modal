import streamlit as st

st.set_page_config(page_title="Home")
st.title("Coffee Shop Financial Projection App")

st.write(
    """
Welcome to the Coffee Shop Financial Projection App! This app helps you to project and analyze the financial performance of opening new coffee shops in various locations.

**Features:**
- **Edit Location Details**: Add or edit the details of various coffee shop locations, including sales volume, monthly fixed costs, and initial opening costs.
- **Run Financial Projection Simulation**: Based on the entered location details, simulate and visualize the cumulative net profit over 6 months.

**How to Use:**
1. Navigate to the "Edit Location Details" page from the sidebar to add or modify the details of your coffee shop locations.
2. Go to the "Run Financial Projection Simulation" page to see the financial projections based on your inputs.
"""
)
