# Roast & Code Café ☕ Expansion Simulation

https://github.com/raoufchebri/scenario-analysis-neon-modal/assets/13738772/1d86c8d6-8c9c-47b4-9c3d-dd4910ea32b5

## Overview

Roast & Code Café ☕ is a place to explore a wide range of roasted coffee, and is increasing in popularity, especially among Python developers.
In this project, we will run scenario analysis that will help determine when and where Roast & Code Café ☕ should open their next shops.
This app features a Streamlit interface for interactive use and utilizes Neon Postgres for data storage.

## Setup

To get started, ensure you have Python and a [Neon Postgres account](https://console.neon.tech).

Create and activate a Python environement using the following commands:

```bash
python -m venv my env
source env/bin/activate
```

You will also need Streamlit and other Python libraries, which can be installed using pip:

```bash
pip install streamlit pandas plotly psycopg2-binary python-dotenv
```

### Database Setup

Before running the application, set up the necessary tables in your Neon Postgres database. The following SQL script (`seed.sql`) can be used to create the required tables:

```sql
CREATE TABLE cumulative_net_profits (
    simulation_name VARCHAR(255) NOT NULL,
    week INT NOT NULL,
    cumulative_net_profit DECIMAL NOT NULL,
    PRIMARY KEY (simulation_name, week)
);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) UNIQUE NOT NULL,
    sales_volume INT NOT NULL,
    monthly_fixed_costs INT NOT NULL,
    initial_opening_cost INT NOT NULL
);
```

Run this SQL script in your Postgres environment to create the tables, or run the following command:

```bash
psql 'YOUR_CONNECTION_STRING' -f seed.sql

```

### Environment Variables

The application requires several environment variables to be set for database connection and other configurations.

Run the below command to copy and create a `.env` file in the project root directory:

```bash
mv ".env copy" .env
```

Your `.env` file should look like this:

```
NEON_PROJECT_ID=<your_project_id>
NEON_API_KEY=<your_neon_api_key>
PGUSER=<your_postgres_user>
PGPASSWORD=<your_postgres_password>
```

Replace the placeholder values with your Postgres credentials and Neon project details.

### Find your Neon Project ID

You can find your Neon Project ID under the `Project Settings` tab.
<img width="1701" alt="Screenshot 2024-03-20 at 16 06 37" src="https://github.com/raoufchebri/scenario-analysis-neon-modal/assets/13738772/16b52474-4c1a-47c2-a56b-192770bb0781">

### Create a Neon API key

To create a Neon API key, naviagte to your account settings and click on `API Keys`. Click on `Generate a New API Key`, give a name to your API key and click `Create`.

<img width="1035" alt="Screenshot 2024-03-20 at 16 06 18" src="https://github.com/raoufchebri/scenario-analysis-neon-modal/assets/13738772/d0770e51-2bd4-44e0-a9d5-1803cd93e22e">

## Running the Application

Navigate to the project directory in your terminal and run the Streamlit application using:

```bash
streamlit run app.py
```

This command will start the Streamlit server, and you should be able to access the application by navigating to the URL provided in the terminal output.

## Scenario Analysis

### Create a new location

To run a simulation, you first need to add potential locations you're looking to open a new shop.
Each location has its projected average daily sales volume, monthly fixed costs, and an initial opening cost.

The default scenario name is called `main`, and is also the parent branch. Each scenario is effectively a Postgres branch derived from `main`.
[More about Neon Postgres branches](https://neon.tech/docs/introduction/branching).
You can save new locations in the current scenario, or in a new one.

### Run simulations

To run a simulaiton, you can select your locations and specify when you plan to open a new location in the next 26 weeks.
You can select multiple locations and add comma seperated opening weeks.
<img width="1701" alt="Screenshot 2024-03-20 at 16 29 26" src="https://github.com/raoufchebri/scenario-analysis-neon-modal/assets/13738772/5cca8071-44f7-4c40-aa82-caadb7a5bc1a">
