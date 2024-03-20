from dotenv import load_dotenv
import psycopg2
import requests
import os
import streamlit as st

# Load environment variables
load_dotenv()

# Environment variables
project_id = os.getenv("NEON_PROJECT_ID")
api_key = os.getenv("NEON_API_KEY")
db_user = os.getenv("PGUSER")
db_password = os.getenv("PGPASSWORD")
base_url = f"https://console.neon.tech/api/v2/projects/{project_id}/branches"
headers = {"accept": "application/json", "authorization": f"Bearer {api_key}"}


def get_branches():
    response = requests.get(base_url, headers=headers)
    branches = [
        (branch["id"], branch["name"]) for branch in response.json()["branches"]
    ]
    return branches


def create_branch_and_get_host(project_id, scenario_name):
    url = f"https://console.neon.tech/api/v2/projects/{project_id}/branches"
    payload = {"branch": {"name": scenario_name}, "endpoints": [{"type": "read_write"}]}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        branch_info = response.json()
        host = branch_info["endpoints"][0]["host"]
        return host
    else:
        st.error("Failed to create branch.")
        return None


# Fetch host for a given branch ID
def get_db_host(branch_id):
    url = f"{base_url}/{branch_id}/endpoints"
    response = requests.get(url, headers=headers)
    host = response.json()["endpoints"][0]["host"]
    return host


# Connect to database using dynamic host
def connect_db(host):
    conn = psycopg2.connect(
        user=db_user,
        password=db_password,
        host=host,
        database="neondb",
        sslmode="require",
    )
    return conn


def get_locations(host):
    conn = connect_db(host)
    cur = conn.cursor()
    cur.execute(
        "SELECT location_name, sales_volume, monthly_fixed_costs, initial_opening_cost FROM locations;"
    )
    locations = cur.fetchall()
    cur.close()
    conn.close()
    return locations


def save_location_to_db(
    location_name, sales_volume, monthly_fixed_costs, initial_opening_cost, host
):
    conn = connect_db(host)  # Now passing the dynamic host
    cur = conn.cursor()
    try:
        # Your UPSERT query remains the same
        cur.execute(
            """
        INSERT INTO locations (location_name, sales_volume, monthly_fixed_costs, initial_opening_cost)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (location_name) DO UPDATE SET
        sales_volume = EXCLUDED.sales_volume,
        monthly_fixed_costs = EXCLUDED.monthly_fixed_costs,
        initial_opening_cost = EXCLUDED.initial_opening_cost;
        """,
            (location_name, sales_volume, monthly_fixed_costs, initial_opening_cost),
        )
        conn.commit()
        st.success(f"Location details saved for {location_name}!")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()


def save_simulation_to_db(simulation_name, simulation_results, host):
    conn = connect_db(host)
    cur = conn.cursor()
    for i, net_profit in enumerate(simulation_results, start=1):
        cur.execute(
            """
            INSERT INTO cumulative_net_profits (simulation_name, week, cumulative_net_profit)
            VALUES (%s, %s, %s)
            """,
            (simulation_name, i, float(net_profit)),
        )
    conn.commit()
    cur.close()
    conn.close()


def fetch_simulation_names_from_db(host):
    conn = connect_db(host)
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT simulation_name FROM cumulative_net_profits ORDER BY simulation_name"
    )
    simulation_names = cur.fetchall()
    cur.close()
    conn.close()
    return [name[0] for name in simulation_names]

def fetch_simulation_data_from_db(simulation_name, host):
    conn = connect_db(host)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT week, cumulative_net_profit
        FROM cumulative_net_profits
        WHERE simulation_name = %s
        ORDER BY week
    """,
        (simulation_name,),
    )
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data
