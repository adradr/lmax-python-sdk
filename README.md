# lmax-python-sdk
Unofficial LMAX Python SDK

This is a Python SDK for interacting with the LMAX trading platform. It provides a set of modules to interact with different aspects of the platform. Since the OpenAPI generator is messy and I needed to interact with LMAX rather implemented a very lightweight and simple SDK.

## Modules
### Client
The client module, located in `lmax_python_sdk/client.py`, provides the LMAXClient class for interacting with the LMAX API. It uses the `client_key_id` for authentication.

### Websocket client
Using the base client, the websocket client is located at `lmax_python_sdk/ws_client.py`. It provides easy access to the websocket streams by using the same argument format and authentication as the base client. 

### Validation
The validation module, located in `lmax_python_sdk/validation.py`, provides various validation functions and constants. Contains different `enum` types for categorical input arguments.

### Account
The account module, located in `lmax_python_sdk/account`, provides functionality related to account data and trading.

### Broker Market Data
The broker allows to access the real-time and historical LMAX data for close prices and orderbook level data.

### Public Data
Not implemented.

## Example Usage
Here are some examples of how to use these modules. For more depth take a look at the [docs page.](https://adradr.github.io/lmax-python-sdk/)

### REST API
```
import os
import lmax_python_sdk

lmax_client = lmax_python_sdk.account.account_data.LMAXAccount(
    client_key_id=os.getenv("LMAX_DEMO_API_KEY"),
    secret=os.getenv("LMAX_DEMO_API_SECRET"),
    base_url=lmax_python_sdk.ClientBaseURLType.ACCOUNT_LONDON_DEMO,
)

lmax_client.get_instrument_data_symbol("EUR/USD")

[{'instrument_id': 'eur-usd',
  'security_id': '4001',
  'symbol': 'EUR/USD',
  'currency': 'USD',
  'unit_of_measure': 'EUR',
  'quantity_increment': '1000.0000',
  'margin': '1.00',
  'minimum_position_size': '1000.0000',
  'maximum_position_size': '500000000.0000',
  'trading_days': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
  'open_time': '17:05',
  'close_time': '17:00',
  'time_zone': 'America/New_York',
  'minimum_commission': '0.00000',
  'aggressive_commission_rate': '0.25000',
  'passive_commission_rate': '0.25000',
  'price_increment': '0.000010',
  'minimum_price': '0.000000',
  'maximum_price': '99999.000000',
  'short_swap_points': '-0.510',
  'long_swap_points': '0.950',
  'short_swap_cost': '-0.51000',
  'long_swap_cost': '-0.95000',
  'swap_cost_units': '10000.0000',
  'trade_date': '2024-02-08',
  'value_date_from': '2024-02-12',
  'value_date_to': '2024-02-13',
  'asset_class': 'CURRENCY'}]
```

### Websocket
During testing it did not work with a demo access (`INSUFFICIENT_PERMISSIONS`), not sure if it needs to be enabled but it has been tested with the production access and worked perfectly.
```
ws = lax_python_sdk.ws_client.LMAXWebSocketClient(
    client_key_id=os.getenv("LMAX_API_KEY"),
    secret=os.getenv("LMAX_API_SECRET"),
    base_url=lmax_python_sdk.ClientBaseURLType.MARKET_DATA_LONDON_PROFESSIONAL,
    verbose=True
)
ws.subscribe({"name": "TRADE", "instruments": ["eur-usd"]})
ws.connect()
```
