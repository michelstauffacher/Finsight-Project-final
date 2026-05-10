import streamlit as st # Import the streamlit library
import yfinance as yf # Import the yfinance library
import pandas as pd # Import the pandas library
from sklearn.model_selection import train_test_split # Import the train_test_split function
from sklearn.neighbors import KNeighborsClassifier # Import the KNeighborsClassifier class
from sklearn.preprocessing import MinMaxScaler # Import the MinMaxScaler class

# This function is used to format large numbers in a readable format
def format_large_number(val): # Initialising the format_large_number function
    if val is None or pd.isna(val) or val == 0: # If the value is None, isna, or 0, return "N/A"
        return "N/A" # Return "N/A" if the value is None, isna, or 0
    abs_val = abs(val) # Get the absolute value of the value
    if abs_val >= 1e12: return f"${val / 1e12:,.2f}T" # If the absolute value is greater than or equal to 1e12 (1 trillion), return the value in trillions
    if abs_val >= 1e9: return f"${val / 1e9:,.2f}B" # If the absolute value is greater than or equal to 1e9 (1 billion), return the value in billions
    if abs_val >= 1e6: return f"${val / 1e6:,.2f}M" # If the absolute value is greater than or equal to 1e6 (1 million), return the value in millions
    return f"${val:,.0f}" # If the absolute value is less than 1e6 (1 thousand), return the value in thousands

# This code block is used to show the title for the stock valuation
st.title("FinSight Stock Valuation") # Show the title for the stock valuation

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

# Check if the ticker is in the session state and if not, show an error message and stop the program
if "ticker" not in st.session_state: # If the ticker is not in the session state, show an error
    st.error("No stock selected. Please search.") # Show an error message
    st.stop() # Stop the program

# This code block is used to get the ticker and symbol from the session state
if "ticker" in st.session_state: # If the ticker is in the session state, show the divider
    st.divider()
    ticker = st.session_state["ticker"] # Get the ticker from the session state
    symbol = str(ticker).upper() # Get the symbol from the ticker

    # Centralized data fetching for Yahoo Finance
    if "yf_data" not in st.session_state or st.session_state.get("data_ticker") != ticker: # If the yf_data is not in the session state or the data_ticker is not the ticker, show a spinner
        with st.spinner(f"Getting {symbol}..."):
            stock = yf.Ticker(ticker) # Get the stock from the ticker
            st.session_state["yf_data"] = { # Set the yf_data to the session state
                "info": stock.info, # Set the info to the session state
                "history": stock.history(period="5y") # Set the history to the session state
            }
            st.session_state["data_ticker"] = ticker # Set the data_ticker to the session state

    # This code block is used to get the info and history from the session state
    info = st.session_state["yf_data"]["info"] # Get the info from the session state
    df_history = st.session_state["yf_data"]["history"] # Get the history from the session state

    # This code block is used to show the title, sector, and industry
    st.title(f"{info.get('longName')} ({symbol})") # Show the title
    st.write(f"Sector: {info.get('sector')} - Industry: {info.get('industry')}") # Show the sector and industry
    st.divider()

    # This code block is used to show the metrics
    col1, col2, col3, col4 = st.columns(4) # Create 4 columns for the metrics                       
    col1.metric("Current Price", f"${info.get('currentPrice', 'N/A')}") # Show the current price
    mkt_cap = info.get('marketCap') # Get the market cap from the info
    col2.metric("Market Cap", format_large_number(mkt_cap)) # Show the market cap
    col3.metric("P/E Ratio", info.get('trailingPE', 'N/A')) # Show the P/E ratio
    col4.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}") # Show the 52 week high

    # This code block is used to show the revenue, EPS, dividend yield, and 52 week low
    col1, col2, col3, col4 = st.columns(4) # Create 4 columns for the metrics
    rev = info.get('totalRevenue') # Get the revenue from the info
    col1.metric("Revenue", format_large_number(rev)) # Show the revenue
    col2.metric("EPS", info.get('trailingEps', 'N/A')) # Show the EPS
    col3.metric("Dividend Yield", info.get('dividendYield', 'N/A')) # Show the dividend yield
    col4.metric("52W Low", f"${info.get('fiftyTwoWeekLow', 'N/A')}") # Show the 52 week low

    # This code block is used to show the divider
    st.divider() # Show the divider

    # This code block is used to show the price history
    st.subheader("Price History") # Show the subheader
    if not df_history.empty: # If the history is not empty, ...
        chart_years = st.selectbox("Period (Years)", [1, 2, 3, 4, 5], index=1, key="overview_chart_period") # Show the select box for the period
        n_days = min(chart_years * 252, len(df_history)) # Calculate the number of days
        st.line_chart(df_history['Close'].tail(n_days), use_container_width=True) # Show the line chart
    else: # If the history is empty, ...
        st.info("No data.") # Show the info
    
    # This code block is used to show the divider
    st.divider() # Show the divider

    # This code block is used to show the company description
    st.write(info.get('longBusinessSummary', 'No description available')) # Show the description    

# This code block is used to show the divider
st.divider() # Show the divider

# Machine Learning Prediction
st.title(f"KNN Prediction - {ticker}")

# This code block is used to calculate the features and target from the dataframe
df = st.session_state["yf_data"]["history"].copy() # Get the history from the session state
df["return_1d"] = df["Close"].pct_change() # Calculate the 1 day return
df["return_5d"] = df["Close"].pct_change(5) # Calculate the 5 day return
df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int) # Calculate the target
df["return_10d"] = df["Close"].pct_change(10) # Calculate the 10 day return
df["return_20d"] = df["Close"].pct_change(20) # Calculate the 20 day return
df["volatility"] = df["Close"].pct_change().rolling(10).std() # Calculate the volatility
df["ma_ratio_20"] = df["Close"] / df["Close"].rolling(20).mean() # Calculate the 20 day MA ratio
df["ma_ratio_50"] = df["Close"] / df["Close"].rolling(50).mean() # Calculate the 50 day MA ratio
df["volume_change"] = df["Volume"].pct_change() # Calculate the volume change
df = df.dropna() # Drop the na values

# This code block is used to get the features and target from the dataframe
X = df[["return_1d", "return_5d", "return_10d", "return_20d", "volatility", "ma_ratio_20", "ma_ratio_50", "volume_change"]] # Get the features from the dataframe
y = df["target"] # Get the target from the dataframe

# This code block is used to split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.75, shuffle=False) # Split the data into training and testing sets

# This code block is used to initialize the scaler and fit the scaler to the training data
scaler = MinMaxScaler() # Initialize the scaler
X_train_scaled = scaler.fit_transform(X_train) # Fit the scaler to the training data
X_test_scaled = scaler.transform(X_test) # Transform the testing data

# This code block is used to initialize the KNN classifier and fit the classifier to the training data
knn = KNeighborsClassifier(n_neighbors=20) # Initialize the KNN classifier
knn.fit(X_train_scaled, y_train)

# This code block is used to show the test accuracy
st.metric("Test Accuracy", f"{knn.score(X_test_scaled, y_test):.1%}") # Show the test accuracy

# This code block is used to transform the latest data and predict the target
latest = scaler.transform(X.iloc[[-1]]) # Transform the latest data
prediction = knn.predict(latest)[0] # Predict the target
st.subheader("Tomorrow's Prediction") # Show the subheader
st.write("📈 UP" if prediction == 1 else "📉 DOWN") # Show the prediction   