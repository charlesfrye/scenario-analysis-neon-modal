import modal
import streamlit as st

from backend import db

st.title("Roast & Code Café ☕ Locations")

api_client = modal.Cls.lookup("coffeeshop-neon-client", "ApiClient")()

branches = api_client.get_branches.remote()
branch_options = [branch[1] for branch in branches]
selected_branch_name = st.selectbox("Select a Scenario", branch_options)
selected_branch_id = [
    branch[0] for branch in branches if branch[1] == selected_branch_name
][0]

# Display locations based on selected branch
DbClient = modal.Cls.lookup("coffeeshop-neon-client", "DbClient")
host = api_client.get_host.remote(selected_branch_id)
client = DbClient(host)
location_names = db.location.get_locations(client)
selected_location = st.selectbox(
    "Select an existing location (optional)", [""] + location_names
)

if "locations" not in st.session_state:
    st.session_state["locations"] = {}


def save_location_details():
    location_name = st.session_state.location_name
    sales_volume = st.session_state.sales_volume
    monthly_fixed_costs = st.session_state.monthly_fixed_costs
    initial_opening_cost = st.session_state.initial_opening_cost
    st.session_state["locations"][location_name] = {
        "sales_volume": sales_volume,
        "monthly_fixed_costs": monthly_fixed_costs,
        "initial_opening_cost": initial_opening_cost,
    }
    st.success(f"Details saved for {location_name}!")
    db.location.save_location(
        client,
        location_name,
        sales_volume,
        monthly_fixed_costs,
        initial_opening_cost,
    )


st.text_input("Location Name", key="location_name", value=selected_location)
st.number_input("Daily Sales Volume (cups)", min_value=0, value=100, key="sales_volume")
st.number_input(
    "Monthly Fixed Costs ($)", min_value=0, value=3000, key="monthly_fixed_costs"
)
st.number_input(
    "Initial Opening Cost ($)", min_value=0, value=15000, key="initial_opening_cost"
)

col1, col2 = st.columns(2)
with col1:
    if st.button("Save Location Details"):
        save_location_details()

with col2:
    if st.button("Save in a New Scenario"):
        st.session_state["show_scenario_name_input"] = True

if (
    "show_scenario_name_input" in st.session_state
    and st.session_state["show_scenario_name_input"]
):
    scenario_name = st.text_input("Enter the name of the scenario", key="scenario_name")
    if st.button("Save Scenario"):
        host = api_client.create_branch_and_get_host.remote(scenario_name)
        st.success("Scenario created.")
        if host:
            save_location_details()
            st.success("Scenario saved.")
            branches = api_client.get_branches.remote()
        del st.session_state["show_scenario_name_input"]
