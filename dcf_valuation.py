import pandas as pd # Import the pandas library
import streamlit as st # Import the streamlit library
import yfinance as yf # Import the yfinance library

# Sidebar Search (see home.py for more details)
with st.sidebar:
    st.header("Search Stock")
    with st.form("sidebar_search"):
        ticker_input = st.text_input("Enter Ticker", placeholder="e.g. AAPL")
        search_clicked = st.form_submit_button("Search", use_container_width=True)

    if search_clicked and ticker_input:
        search = yf.Search(ticker_input)
        results = search.quotes
        options = {}
        for r in results:
            name = r.get("shortname") or r.get("longname", "Unknown")
            symbol = r.get("symbol", "")
            if symbol:
                options[f"{name} ({symbol})"] = symbol
        st.session_state["options"] = options

    if "options" in st.session_state and st.session_state["options"]:
        selected = st.selectbox("Select a company", list(st.session_state["options"].keys()))
        if st.button("Analyse", use_container_width=True):
            st.session_state["ticker"] = st.session_state["options"][selected]
            st.switch_page("home.py")

# Check if the ticker is in the session state and if not, show an error message and stop the program
if "ticker" not in st.session_state: # If the ticker is not in the session state, show an error
    st.error("No stock selected. Please search.") # Show an error message
    st.stop() # Stop the program

# Get the ticker from the session state and convert it to uppercase
ticker = st.session_state["ticker"].upper() # Get the ticker from the session state and convert it to uppercase
st.title(f"DCF Valuation - {ticker}") # Show the title with the ticker

# Function to get the value of the key
def get_value(info, key): # Initialising the get_value function
    val = info.get(key) # Get the value of the key
    return float(val) if val is not None else 0.0 # Return the value of the key

# Function to format the large numbers in a readable format
def format_large_number(val): # Initialising the format_large_number function
    if val is None or pd.isna(val) or val == 0: # If the value is None, isna, or 0, return "N/A"
        return "N/A" # Return "N/A" if the value is None, isna, or 0
    abs_val = abs(val) # Get the absolute value of the value
    if abs_val >= 1e12: return f"${val / 1e12:,.2f}T" # If the absolute value is greater than or equal to 1e12 (1 trillion), return the value in trillions
    if abs_val >= 1e9: return f"${val / 1e9:,.2f}B" # If the absolute value is greater than or equal to 1e9 (1 billion), return the value in billions
    if abs_val >= 1e6: return f"${val / 1e6:,.2f}M" # If the absolute value is greater than or equal to 1e6 (1 million), return the value in millions
    return f"${val:,.0f}" # If the absolute value is less than 1e6 (1 thousand), return the value in thousands

# Function to calculate the metrics for the DCF valuation
def calculate_metrics(info, assumptions): # Initialising the calculate_metrics function
    revenue_0 = get_value(info, "totalRevenue") # Get the value of the total revenue
    cash_0 = get_value(info, "totalCash") # Get the value of the total cash
    debt_0 = get_value(info, "totalDebt") # Get the value of the total debt
    shares_0 = get_value(info, "sharesOutstanding") # Get the value of the shares outstanding
    price_0 = get_value(info, "currentPrice") # Get the value of the current price

    # Fallback for sharesOutstanding if not directly available (e.g., for some ETFs)
    if shares_0 <= 0 and price_0 > 0: # If the shares outstanding is less than or equal to 0 and the price is greater than 0, ...
        market_cap = get_value(info, "marketCap") # Get the value of the market cap
        if market_cap > 0: # If the market cap is greater than 0, ...
            shares_0 = market_cap / price_0 # Set the shares outstanding to the market cap divided by the share price

    # Fallback for totalRevenue if not directly available (e.g., for some ETFs)
    if revenue_0 <= 0: # If the total revenue is less than or equal to 0, ...
        revenue_per_share = get_value(info, "revenuePerShare") # Get the value of the revenue per share
        if revenue_per_share > 0 and shares_0 > 0: # If the revenue per share is greater than 0 and the shares outstanding is greater than 0, ...
            revenue_0 = revenue_per_share * shares_0 # Set the total revenue to the revenue per share multiplied by the shares outstanding
        else: # If the revenue per share is not greater than 0 or the shares outstanding is not greater than 0, ...
            gross_profits = get_value(info, "grossProfits") # Get the value of the gross profits
            if gross_profits > 0: # If the gross profits is greater than 0, ...
                revenue_0 = gross_profits / 0.3  # Assume 30% gross margin

    # Get the company name from the info or the ticker
    company_name = str(info.get("longName") or ticker) # Get the company name from the info or the ticker

    years = int(assumptions["years"]) # Get the number of years from the assumptions
    growth = float(assumptions["revenue_growth"]) # Get the revenue growth from the assumptions
    ebit_margin = float(assumptions["ebit_margin"]) # Get the EBIT margin from the assumptions
    tax_rate = float(assumptions["tax_rate"]) # Get the tax rate from the assumptions
    da_pct = float(assumptions["da_pct"]) # Get the D&A percentage from the assumptions
    capex_pct = float(assumptions["capex_pct"]) # Get the Capex percentage from the assumptions
    nwc_pct = float(assumptions["nwc_pct"]) # Get the NWC percentage from the assumptions
    wacc = float(assumptions["wacc"]) # Get the WACC from the assumptions
    terminal_growth = float(assumptions["terminal_growth"]) # Get the terminal growth from the assumptions

    # Code block used to calculate the metrics for the DCF valuation
    rows = [] # Initialize the rows variable
    previous_revenue = revenue_0 # Set the previous revenue to the revenue
    for year in range(1, years + 1): # For Loop that loops through the years (1 to the number of years + 1)
        revenue = previous_revenue * (1 + growth) # Calculate the revenue
        ebit = revenue * ebit_margin # Calculate the EBIT
        nopat = ebit * (1 - tax_rate) # Calculate the NOPAT
        depreciation = revenue * da_pct # Calculate the depreciation
        capex = revenue * capex_pct # Calculate the Capex
        change_nwc = (revenue - previous_revenue) * nwc_pct # Calculate the change in NWC
        fcff = nopat + depreciation - capex - change_nwc # Calculate the FCFF
        rows.append( # Append the rows to the rows variable
            {
                "Year": year, # Set the year
                "Revenue": revenue, # Set the revenue
                "EBIT": ebit, # Set the EBIT
                "NOPAT": nopat, # Set the NOPAT
                "Depreciation": depreciation,
                "Capex": capex, # Set the Capex
                "Change NWC": change_nwc, # Set the change in NWC
                "FCFF": fcff, # Set the FCFF
            }
        )
        previous_revenue = revenue # Set the previous revenue to the revenue

    # This code block is used to calculate the discount factors and the PV FCFF
    projection = pd.DataFrame(rows) # Set the projection to the rows
    discount_factors = [1 / ((1 + wacc) ** y) for y in projection["Year"]] # Calculate the discount factors
    projection["Discount Factor"] = discount_factors # Set the discount factors to the projection
    projection["PV FCFF"] = projection["FCFF"] * projection["Discount Factor"] # Calculate the PV FCFF
    pv_fcff = float(projection["PV FCFF"].sum()) # Calculate the PV FCFF

    terminal_value = 0.0 # Set the terminal value to 0
    if wacc > terminal_growth: # If the WACC is greater than the terminal growth, ... (Note: this ensures that the terminal value is not negative)
        last_fcff = float(projection["FCFF"].iloc[-1]) # Get the last FCFF
        terminal_value = (last_fcff * (1 + terminal_growth)) / (wacc - terminal_growth) # Calculate the terminal value
    pv_terminal = terminal_value / ((1 + wacc) ** years) # Calculate the PV terminal

    enterprise_value = pv_fcff + pv_terminal # Calculate the enterprise value as the sum of the PV FCFF and the PV terminal
    net_debt = debt_0 - cash_0 # Calculate the net debt as the total debt minus the total cash
    equity_value = enterprise_value - net_debt # Calculate the equity value

    fair_value_per_share = 0.0 # Set the fair value per share to 0
    if shares_0 > 0: # If the shares outstanding is greater than 0, ...
        fair_value_per_share = equity_value / shares_0 # Calculate the fair value per share as the equity value divided by the shares outstanding

    # This return statement returns a dictionary of the metrics for the DCF valuation
    return {
        "projection": projection, # Set the projection to the projection
        "enterprise_value": enterprise_value, # Set the enterprise value to the enterprise value
        "equity_value": equity_value, # Set the equity value to the equity value
        "fair_value_per_share": fair_value_per_share, # Set the fair value per share to the fair value per share
        "price_0": price_0, # Set the price to the price
        "terminal_is_valid": wacc > terminal_growth, # Set the terminal is valid to the terminal is valid
        "pv_fcff": pv_fcff, # Set the PV FCFF to the PV FCFF
        "pv_terminal": pv_terminal, # Set the PV terminal to the PV terminal
        "net_debt": net_debt, # Set the net debt to the net debt
        "company_name": company_name, # Set the company name to the company name
    }

# This function is used to render the metrics for the DCF valuation
def render_metrics(ticker, metrics): # initialising the render_metrics function
    name = metrics["company_name"] # Get the company name from the metrics
    if name == "": # If the company name is empty, ...
        name = ticker # Set the company name to the ticker
    st.subheader(name) # Show the company name

    c1, c2, c3, c4 = st.columns(4) # Create 4 columns for the metrics

    c1.metric("Enterprise Value", format_large_number(metrics["enterprise_value"])) # Show the enterprise value in a readable format, thanks due to the format_large_number function
    c2.metric("Equity Value", format_large_number(metrics["equity_value"])) # Show the equity value in a readable format, thanks due to the format_large_number function

    if metrics["fair_value_per_share"] > 0: # If the fair value per share is greater than 0, ...
        if metrics["price_0"] > 0: # If the price is greater than 0, ...
            is_above = metrics["fair_value_per_share"] > metrics["price_0"] # Calculate if the fair value per share is above the price
            c3.metric(
                label="Fair Value / Share", # Show the label for the fair value per share
                value=f"${metrics['fair_value_per_share']:,.2f}", # Show the fair value per share in a readable format
                delta="+ Above Market" if is_above else "- Below Market", # Show the delta for the fair value per share (and to show if it is above or below the market)
            )
        else: # If the price is not greater than 0, ...
            c3.metric("Fair Value / Share", f"${metrics['fair_value_per_share']:,.2f}") # Show the fair value per share in a readable format
    else: # For the third column, if the fair value per share is not greater than 0, ...
        c3.metric("Fair Value / Share", "N/A") # Show the fair value per share as "N/A"

    # This code block is used to show the current price
    if metrics["price_0"] > 0: # If the price is greater than 0, ...
        c4.metric("Current Price (Yahoo)", f"${metrics['price_0']:,.2f}") # Show the current price in a readable format thanks to the format_large_number function
    else: # If the price is not greater than 0, ...
        c4.metric("Current Price (Yahoo)", "N/A") # Show the current price as "N/A"

    if not metrics["terminal_is_valid"]: # If the terminal is not valid (i.e. the terminal growth is greater than the WACC), ...
        st.warning("Terminal growth must be lower than WACC for a valid terminal value.") # Show a warning message

# This function is used to render the tables for the DCF valuation
def render_tables(metrics): # initialising the render_tables function 
    table = metrics["projection"].copy() # Copy the projection to the table, so we can modify it without affecting the original projection
    table["EBIT Margin"] = table["EBIT"] / table["Revenue"] # Calculate the EBIT margin

    # This code block is used to show the DCF projection table as well as the valuation bridge
    st.write("DCF Projection Table") # Show the title for the DCF projection table
    st.dataframe( # Show the dataframe for the DCF projection table
        table.style.format( # Format the dataframe for the DCF projection table
            {
                "Revenue": "{:,.0f}", # Show the revenue in a readable format
                "EBIT": "{:,.0f}", # Show the EBIT in a readable format
                "NOPAT": "{:,.0f}", # Show the NOPAT in a readable format
                "Depreciation": "{:,.0f}", # Show the depreciation in a readable format
                "Capex": "{:,.0f}", # Show the Capex in a readable format
                "Change NWC": "{:,.0f}", # Show the change in NWC in a readable format
                "FCFF": "{:,.0f}", # Show the FCFF in a readable format
                "Discount Factor": "{:.3f}", # Show the discount factor in a readable format
                "PV FCFF": "{:,.0f}", # Show the PV FCFF in a readable format
                "EBIT Margin": "{:.0%}", # Show the EBIT margin in a readable format
            }
        ), # Format the dataframe for the DCF projection table
        use_container_width=True, # Use the container width
        height=420, # Set the height of the dataframe to 420 pixels, so it perfectly fits the maximum forecast horizon
    )

    # This code block is used to show the valuation bridge
    bridge_rows = [ # Initialize the bridge rows variable, which is a list of the items and their values in the valuation bridge
        ["PV of Explicit FCFF", metrics["pv_fcff"] / 1_000_000], # Show the PV of Explicit FCFF in a readable format
        ["PV of Terminal Value", metrics["pv_terminal"] / 1_000_000], # Show the PV of Terminal Value in a readable format
        ["Enterprise Value", metrics["enterprise_value"] / 1_000_000], # Show the Enterprise Value in a readable format
        ["Less: Net Debt", -metrics["net_debt"] / 1_000_000], # Show the Less: Net Debt in a readable format
        ["Equity Value", metrics["equity_value"] / 1_000_000], # Show the Equity Value in a readable format
    ]
    # This code block is used to create the bridge dataframe (i.e. the valuation bridge table)
    bridge = pd.DataFrame(bridge_rows, columns=["Item", "Value (USD mm)"]) # Create the bridge dataframe

# This code block is used to check if the data is loaded on the Home page
if "yf_data" not in st.session_state or st.session_state.get("data_ticker") != ticker: # Using a guard to check if the data is loaded on the Home page
    st.error("Data not loaded. Please go to the Home page and click 'Analyse' first.") # Show an error message
    st.stop() # Stop the program

# This code block is used to get the info (i.e. the company information) from the session state
info = st.session_state["yf_data"]["info"] # Get the info from the session state

# This code block is used to check if the info is loaded
if not info: # If the info is not loaded, ...
    st.error("Could not load data.") # Show an error message
    st.stop() # Stop the program

# This code block is used to check if the revenue is loaded on the Home page
revenue_0_check = get_value(info, "totalRevenue") # Get the revenue from the info
if revenue_0_check <= 0: # If the revenue is less than or equal to 0, ...
    revenue_per_share = get_value(info, "revenuePerShare") # Get the revenue per share from the info
    shares_check = get_value(info, "sharesOutstanding") # Get the shares outstanding from the info
    if not (revenue_per_share > 0 and shares_check > 0) and get_value(info, "grossProfits") <= 0: # If the revenue per share is not greater than 0 and the shares outstanding is not greater than 0 and the gross profits is less than or equal to 0, ...
        st.error("Yahoo Finance did not return a usable revenue value for this ticker. DCF cannot proceed.") # Show an error message
        st.stop() # Stop the program

# Default slider inputs
default_revenue_growth = 0.10
default_ebit_margin = 0.15
default_tax_rate = 0.21
default_da_pct = 0.03
default_capex_pct = 0.04

# Two-column layout: sliders on the left, key metrics on the right
controls, output = st.columns([1, 2])

# This code block is used to show the sliders for the DCF valuation
with controls:
    st.subheader("Assumptions") # Show the subheader for the assumptions
    years = st.slider("Forecast horizon (years)", 3, 10, 5, 1) # Show the slider for the forecast horizon (years)
    revenue_growth = st.slider("Revenue growth (%)", -5.0, 20.0, default_revenue_growth * 100, 0.5) / 100 # Show the slider for the revenue growth (%)
    ebit_margin = st.slider("EBIT margin (%)", 3.0, 50.0, default_ebit_margin * 100, 0.5) / 100 # Show the slider for the EBIT margin (%)
    tax_rate = st.slider("Tax rate (%)", 0.0, 40.0, default_tax_rate * 100, 0.5) / 100 # Show the slider for the tax rate (%)
    da_pct = st.slider("D&A as % of revenue", 0.0, 20.0, default_da_pct * 100, 0.5) / 100 # Show the slider for the D&A as % of revenue
    capex_pct = st.slider("Capex as % of revenue", 0.0, 25.0, default_capex_pct * 100, 0.5) / 100 # Show the slider for the Capex as % of revenue
    nwc_pct = st.slider("Change NWC as % of incremental revenue", 0.0, 15.0, 1.0, 0.5) / 100 # Show the slider for the Change NWC as % of incremental revenue
    wacc = st.slider("WACC (%)", 5.0, 18.0, 8.0, 0.25) / 100 # Show the slider for the WACC (%)
    terminal_growth = st.slider("Terminal growth (%)", 0.0, 5.0, 3.0, 0.25) / 100 # Show the slider for the Terminal growth (%)

# Keep the assumptions in the session state, so we don't have to re-enter them every time we run the program
st.session_state["dcf_assumptions"] = { # Set the assumptions to the session state
    "years": int(years), # Set the years to the years
    "revenue_growth": float(revenue_growth), # Set the revenue growth to the revenue growth
    "ebit_margin": float(ebit_margin), # Set the EBIT margin to the EBIT margin
    "tax_rate": float(tax_rate), # Set the tax rate to the tax rate
    "da_pct": float(da_pct), # Set the D&A as % of revenue to the D&A as % of revenue
    "capex_pct": float(capex_pct), # Set the Capex as % of revenue to the Capex as % of revenue
    "nwc_pct": float(nwc_pct), # Set the Change NWC as % of incremental revenue to the Change NWC as % of incremental revenue
    "wacc": float(wacc), # Set the WACC to the WACC
    "terminal_growth": float(terminal_growth), # Set the Terminal growth to the Terminal growth
}

# This code block is used to calculate the metrics for the DCF valuation
metrics = calculate_metrics(info, st.session_state["dcf_assumptions"]) # Calculate the metrics for the DCF valuation

if metrics is None: # If the metrics are None, ...
    st.error("No calculation") # Show an error message
    st.stop() # Stop the program

# This code block is used to show the metrics and the tables for the DCF valuation  
with output: # Show the metrics and the tables for the DCF valuation in the output column
    render_metrics(ticker, metrics) # Show the metrics for the DCF valuation
    render_tables(metrics) # Show the tables for the DCF valuation