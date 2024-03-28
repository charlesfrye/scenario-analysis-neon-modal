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