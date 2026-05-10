import streamlit as st # Import the streamlit library

# This code block is used to set the page config
st.set_page_config(page_title="FinSight", layout="wide") # Set the page config to the page title and layout

# This code block is used to create a navigation object
pg = st.navigation( # Create a navigation object
    [
        st.Page("home.py", title="FinSight Home"), # Create a page object for the home.py file
        st.Page("stock_price_simulation.py", title="Stock Price Simulation",), # Create a page object for the stock_price_simulation.py file
        st.Page("dcf_valuation.py", title="DCF Valuation"), # Create a page object for the dcf_valuation.py file
    ],
    position="sidebar", # Set the position of the navigation to the sidebar
)
# This code block is used to run the navigation object
pg.run() # Run the navigation object