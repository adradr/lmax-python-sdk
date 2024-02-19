import typing
from .. import client


class LMAXPublicData(client.LMAXClient):

    def get_instrument(self, instrument_id: str) -> typing.Dict[str, str]:
        """
        Get a requested instrument currently available on the platform.

        Args:
        - instrument_id (str): Instrument identifier

        Returns:
        - typing.Dict[str, str]: Returned instrument level data

            ```
                {
                    "instrument_id": "eur-usd",
                    "symbol": "EUR/USD",
                    "security_id": "4001",
                    "currency": "USD",
                    "unit_of_measure": "EUR",
                    "asset_class": "CURRENCY",
                    "quantity_increment": "1000.0000",
                    "price_increment": "0.000010",
                    "ticker_enabled": true
                }
            ```
        """
        endpoint = f"/v1/instruments/{instrument_id}"
        return self._request(endpoint=endpoint, authenticated=False)

    def list_instruments(self) -> typing.List[typing.Dict[str, str]]:
        """
        List all instruments currently available on the platform.

        Returns:
        - typing.List[typing.Dict[str, str]]: List of instruments

            ```
                [
                    {
                        "instrument_id": "eur-usd",
                        "symbol": "EUR/USD",
                        "security_id": "4001",
                        "currency": "USD",
                        "unit_of_measure": "EUR",
                        "asset_class": "CURRENCY",
                        "quantity_increment": "1000.0000",
                        "price_increment": "0.000010",
                        "ticker_enabled": true
                    },
                    {
                        "instrument_id": "gbp-usd",
                        "symbol": "GBP/USD",
                        "security_id": "4002",
                        "currency": "USD",
                        "unit_of_measure": "GBP",
                        "asset_class": "CURRENCY",
                        "quantity_increment": "1000.0000",
                        "price_increment": "0.000010",
                        "ticker_enabled": false
                    }
                ]
            ```
        """
        return self._request(endpoint="/v1/instruments", authenticated=False)

    def get_current_time(self) -> typing.Dict[str, str]:
        """
        Get current time.

        Returns:
        - typing.Dict[str, str]: Current Time
            ```
                {
                    "epoch_millis": "1707346260904",
                    "timestamp": "2024-02-07T22:51:00.904Z"
                }
            ```
        """
        return self._request(endpoint="/v1/time", authenticated=False)

    def get_order_book(
        self,
        instrument_id: str,
    ) -> typing.Dict[str, typing.Union[str, typing.List[typing.Dict[str, str]]]]:
        """
        Get prices for a requested instrument currently on the platform.

        The prices are updated once per second. Once a day, most of our instruments close for 5 minutes.

        A closing price is determined at this time and this will be reflected in the price until the instrument reopens.


        Args:
        - instrument_id (str): Instrument identifier

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[typing.Dict[str, str]]]]: Returned orderbook

            ```
                {
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-02-07T22:51:00.904Z",
                    "status": "OPEN",
                    "bids": [
                                {
                                    "price": "1.181060",
                                    "quantity": "500000.0000"
                                },
                                {
                                    "price": "1.181050",
                                    "quantity": "200000.0000"
                                }
                        ],
                        "asks": [
                                    {
                                        "price": "1.181100",
                                        "quantity": "250000.0000"
                                    },
                                    {
                                        "price": "1.181110",
                                        "quantity": "350000.0000"
                                    }
                        ]
                }
            ```
        """
        endpoint = f"/v1/orderbook/{instrument_id}"
        return self._request(endpoint=endpoint, authenticated=False)

    def get_ticker(self, instrument_id: str) -> typing.Dict[str, str]:
        """
        Get the latest ticker information for an instrument.

        Args:
        - instrument_id (str): Instrument identifier

        Returns:
        - typing.Dict[str, str]: Ticker for instrument

            ```
                {
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-02-07T22:51:00.904Z",
                    "best_bid": "1.180970",
                    "best_ask": "1.181010",
                    "trade_id": "0B5WMAAAAAAAAAAS",
                    "last_quantity": "1000.0000",
                    "last_price": "1.180970",
                    "session_open": "1.181070",
                    "session_low": "1.180590",
                    "session_high": "1.181390",
                }
            ```
        """
        endpoint = f"/v1/ticker/{instrument_id}"
        return self._request(endpoint=endpoint, authenticated=False)
