import numpy as np # Import the numpy library
import pandas as pd # Import the pandas library
import streamlit as st # Import the streamlit library
import yfinance as yf # Import the yfinance library

TRADING_DAYS_PER_YEAR = 252 # Set Trading days per year for later usage

# This function is used to run the Monte Carlo simulation
def run_monte_carlo(prices, years, n_paths, seed): # Initiate a function for the Monte Carlo simulation
    if seed is not None: # If a seed is provided, set the random seed
        np.random.seed(seed) # Set the random seed

    # This code block is used to calculate the log returns, the daily mean, and the daily standard deviation
    log_returns = np.diff(np.log(prices)) # Calculate the log returns
    mu_daily = np.mean(log_returns) # Calculate the daily mean
    sigma_daily = np.std(log_returns) # Calculate the daily standard deviation

    # This code block is used to calculate the total days, the time step, the annual mean, and the annual standard deviation
    total_days = years * TRADING_DAYS_PER_YEAR # Calculate the total days
    dt = 1 / TRADING_DAYS_PER_YEAR # Calculate the time step
    mu_annual = mu_daily * TRADING_DAYS_PER_YEAR # Calculate the annual mean
    sigma_annual = sigma_daily * np.sqrt(TRADING_DAYS_PER_YEAR) # Calculate the annual standard deviation

    # This code block is used to generate the shocks, the drift, and the diffusion
    shocks = np.random.standard_normal((total_days, n_paths)) # Generate the shocks
    drift = (mu_annual - 0.5 * sigma_annual ** 2) * dt # Calculate the drift
    diffusion = sigma_annual * np.sqrt(dt) * shocks # Calculate the diffusion

    # This code block is used to calculate the path returns and the all paths
    path_returns = np.exp(np.cumsum(drift + diffusion, axis=0)) # Calculate the path returns
    all_paths = prices[-1] * np.vstack([np.ones(n_paths), path_returns]) # Calculate the all paths

    # This return statement returns the all paths, the annual mean, and the annual standard deviation
    return all_paths.T, mu_annual, sigma_annual # Return the all paths, the annual mean, and the annual standard deviation

# Search bar is in the sidebar for rapid access
with st.sidebar: # Using a sidebar to show the search bar
    st.header("Search Stock") # Header for the search bar
    with st.form("sidebar_search"): # Form for the search bar
        ticker = st.text_input("Enter Ticker", placeholder="e.g. AAPL") # Text input for the ticker
        search_clicked = st.form_submit_button("Search", use_container_width=True) # Submit button for the search bar

    # This code block is used to search for the ticker and show the options
    if search_clicked and ticker: # If the search button is clicked and the ticker is not empty, ...
        search = yf.Search(ticker) # Search for the ticker
        results = search.quotes # Get the results
        options = {} # Initialize the options dictionary
        for r in results: # Loop through the results
            name = r.get("shortname") or r.get("longname", "Unknown") # Get the name
            symbol = r.get("symbol", "") # Get the symbol
            if symbol: # If the symbol is not empty, ...
                options[f"{name} ({symbol})"] = symbol # Add the option to the options
        st.session_state["options"] = options # Set the options to the session state

    # This code block is used to show the select box for the options
    if "options" in st.session_state and st.session_state["options"]: # If the options are in the session state, show the select box
        selected = st.selectbox("Select a company", list(st.session_state["options"].keys())) # Select the company
        if st.button("Analyse", use_container_width=True): # If the button is clicked, switch to the home page
            st.session_state["ticker"] = st.session_state["options"][selected] # Set the ticker to the session state
            st.switch_page("home.py") # Switch to the home page

# This code block is used to check if the ticker is in the session state and if not, show an error message and stop the program
if "ticker" not in st.session_state: # If the ticker is not in the session state, show an error message and stop the program
    st.error("No stock selected. Please search.") # Show an error message
    st.stop() # Stop the program

# Get the ticker from the session state and convert it to uppercase
ticker = st.session_state["ticker"].upper() # Get the ticker from the session state and convert it to uppercase
st.title(f"DCF Valuation - {ticker}") # Show the title with the ticker

# This code block is used to check if the data is loaded on the Home page
if "yf_data" not in st.session_state or st.session_state.get("data_ticker") != ticker: # Using a guard to check if the data is loaded on the Home page
    st.error("Data not loaded. Please go to the Home page and click 'Analyse' first.") # Show an error message
    st.stop() # Stop the program

# This code block is used to get the history from the session state
df_history_all = st.session_state["yf_data"]["history"] # Get the history from the session state
if df_history_all.empty: # If the history is empty, show an error message and stop the program
    st.error("Could not fetch historical data. Please check the ticker symbol.") # Show an error message
    st.stop() # Stop the program

# This code block is used to show the simulation settings
st.subheader("Simulation Settings") # Show the subheader for the simulation settings
c1, c2, c3, c4 = st.columns(4) # Create 4 columns for the simulation settings
with c1: # Column 1
    n_simulations = st.selectbox("Number of simulations", [100, 500, 1000, 5000], index=2) # Show the select box for the number of simulations
with c2: # Column 2
    history_years = st.selectbox("History window (years)", [1, 2, 3, 4, 5], index=2) # Show the select box for the history window (years)
with c3: # Column 3
    sim_years = st.selectbox("Simulation horizon (years)", [1, 2, 3, 4, 5], index=2) # Show the select box for the simulation horizon (years)
with c4: # Column 4
    use_seed = st.checkbox("Use fixed seed", value=True) # Show the checkbox for the use of a fixed seed
    seed_value = st.number_input( "Seed", min_value=0, value=42, step=1, disabled=not use_seed) # Show the number input for the seed
run_clicked = st.button("Run simulation", type="primary", use_container_width=True) # Show the button for the run simulation    

# This code block is used to check if the run button is not clicked, show an error message and stop the program
if not run_clicked: # If the run button is not clicked, ...
    st.info("Adjust the settings above and click **Run simulation** to start.") # Show an error message
    st.stop() # Stop the program

# This code block is used to slice the cached history to match the requested window
cutoff_date = df_history_all.index[-1] - pd.DateOffset(years=history_years) # Calculate the cutoff date
df_history = df_history_all[df_history_all.index >= cutoff_date] # Slice the history to match the requested window
price_array = df_history["Close"].to_numpy(dtype=float) # Convert the close prices to a numpy array

# This code block is used to run the Monte Carlo simulation
all_paths, mu_annual, sigma_annual = run_monte_carlo( # Run the Monte Carlo simulation
    price_array, # Set the price array
    sim_years, # Set the simulation years
    n_simulations, # Set the number of simulations
    int(seed_value) if use_seed else None,) # Set the seed value

# This code block is used to show the estimated annual drift (mu) and the estimated annual volatility (sigma)
st.write(f"Estimated annual drift (mu): `{mu_annual * 100:.2f}%`") # Show the estimated annual drift (mu)
st.write(f"Estimated annual volatility (sigma): `{sigma_annual * 100:.2f}%`") # Show the estimated annual volatility (sigma)

# This code block is used to show the historical prices
st.subheader("Historical Prices") # Show the subheader for the historical prices
st.line_chart(df_history["Close"].rename("Historical Price"), use_container_width=True)

# This code block is used to convert the all paths to a numpy array
paths_mat = np.array(all_paths).T  # (timesteps, n_paths)

# This code block is used to create the simulation dates
sim_dates = pd.bdate_range( # Create the simulation dates
    start=df_history.index[-1], periods=paths_mat.shape[0], freq="B") # Create the simulation dates

# This code block is used to show the simulation summary
st.subheader("Simulation summary") # Show the subheader for the simulation summary
forecast = pd.DataFrame( # Create the forecast dataframe
    {
        "Mean": np.mean(paths_mat, axis=1), # Calculate the mean
        "5th pct": np.percentile(paths_mat, 5, axis=1), # Calculate the 5th percentile
        "95th pct": np.percentile(paths_mat, 95, axis=1), # Calculate the 95th percentile
    },
    index=sim_dates, # Set the index to the simulation dates
)
st.line_chart(forecast, use_container_width=True) # Show the line chart for the forecast