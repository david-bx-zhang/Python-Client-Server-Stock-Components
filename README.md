A software system of two components (Server and Client)

Server pulls data from Alpha Vantage API (for historical data) and FinnHub API (for live data) to build a consistent intraday price series and simulate a trading strategy

To run this component:
	First export your environment variables: 
		export ALPHAVANTAGE_API_KEY='your_api_key'
		export FINNHUB_API_KEY='your_api_key'

	Set up your email details in config.py (currently using gmail)

To run the server:
	python server.py

To run the client:
	python client.py
