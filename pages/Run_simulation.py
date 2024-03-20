import streamlit as st
import pandas as pd
import plotly.express as px
from db import (
    fetch_simulation_data_from_db,
    fetch_simulation_names_from_db,
    get_branches,
    get_db_host,
    get_locations,
    save_simulation_to_db,
)

st.title("My Next Coffee Shops Simulation")

# Assuming an average price per coffee of $5 and COGS per coffee of $2
average_price = 5
cogs_per_coffee = 2
operating_days = 30  # Assuming 30 operating days in a month

branches = get_branches()
branch_names = [branch[1] for branch in branches]
selected_branch_name = st.selectbox("Select a Branch", branch_names)
selected_branch_id = [
    branch[0] for branch in branches if branch[1] == selected_branch_name
][0]
selected_host = get_db_host(selected_branch_id)


simulation_names = [""] + fetch_simulation_names_from_db(selected_host)
selected_simulation_name = st.selectbox(
    "Select a Simulation", options=simulation_names, index=0
)

# Fetch host and locations for the selected branch
locations = get_locations(
    selected_host
)  # Assuming it now returns detailed location info

# Initialize or update session state as needed
if "simulation_run" not in st.session_state:
    st.session_state["simulation_run"] = False
if "cumulative_net_profit" not in st.session_state:
    st.session_state["cumulative_net_profit"] = pd.Series([])

if selected_simulation_name != "":
    simulation_data_raw = fetch_simulation_data_from_db(
        selected_simulation_name, selected_host
    )
    simulation_data = pd.DataFrame(
        simulation_data_raw, columns=["Week", "Cumulative Net Profit"]
    )
    # Assuming simulation_data is a DataFrame with 'Week' and 'Cumulative Net Profit'
    fig = px.line(
        simulation_data,
        x="Week",
        y="Cumulative Net Profit",
        title=f"Cumulative Net Profit for {selected_simulation_name}",
    )
    fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)


def calculate_cumulative_net_profit_multiple(locations_opening_weeks, weeks=26):
    weekly_net_profit = [0] * weeks
    for location, opening_week in locations_opening_weeks.items():
        _, sales_volume, monthly_fixed_costs, initial_opening_cost = next(
            (item for item in locations if item[0] == location), None
        )
        weekly_sales_volume = sales_volume * 7
        weekly_fixed_costs = monthly_fixed_costs / 4.33
        for week in range(opening_week - 1, weeks):
            weekly_revenue = weekly_sales_volume * average_price
            weekly_variable_costs = weekly_sales_volume * cogs_per_coffee
            weekly_gross_profit = weekly_revenue - weekly_variable_costs
            net_profit = weekly_gross_profit - weekly_fixed_costs
            weekly_net_profit[week] += net_profit
            if week == opening_week - 1:
                weekly_net_profit[week] -= initial_opening_cost
    cumulative_net_profit = pd.Series(weekly_net_profit).cumsum()
    return cumulative_net_profit


def display_location_cashflow_multiple():
    if "simulation_run" not in st.session_state:
        st.session_state["simulation_run"] = False
    if "cumulative_net_profit" not in st.session_state:
        st.session_state["cumulative_net_profit"] = []

    if selected_simulation_name == "":
        location_names = [location[0] for location in locations]
        selected_locations = st.multiselect("Select Locations", options=location_names)
        opening_weeks_input = st.text_input(
            "Enter the opening weeks for the selected locations (comma-separated)", ""
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run Simulation"):
                try:
                    opening_weeks = list(map(int, opening_weeks_input.split(",")))
                    if len(opening_weeks) != len(selected_locations):
                        st.error(
                            "Please enter the same number of opening weeks as the selected locations."
                        )
                    else:
                        locations_opening_weeks = dict(
                            zip(selected_locations, opening_weeks)
                        )
                        simulation_name = "_".join(
                            [
                                f"{loc}-{week}"
                                for loc, week in zip(selected_locations, opening_weeks)
                            ]
                        )
                        st.session_state["cumulative_net_profit"] = (
                            calculate_cumulative_net_profit_multiple(
                                locations_opening_weeks
                            )
                        )
                        st.session_state["simulation_run"] = True
                        st.session_state["simulation_name"] = simulation_name
                except ValueError:
                    st.error("Please enter valid opening weeks as integers.")

        with col2:
            if st.session_state["simulation_run"]:
                if st.button("Save Simulation"):
                    # Ensure this function is defined and handles saving properly
                    save_simulation_to_db(
                        st.session_state["simulation_name"],
                        st.session_state["cumulative_net_profit"],
                        selected_host,
                    )
                    st.success("Simulation results saved successfully.")

        if st.session_state["simulation_run"]:
            # Prepare data for plotting
            weeks = [f"Week {i+1}" for i in range(26)]
            df = pd.DataFrame(
                {
                    "Week": weeks,
                    "Cumulative Net Profit": st.session_state["cumulative_net_profit"],
                }
            )
            # Plotting with Plotly
            fig = px.line(
                df,
                x="Week",
                y="Cumulative Net Profit",
                title=f'Cumulative Net Profit for {st.session_state["simulation_name"]}',
            )
            fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    display_location_cashflow_multiple()
