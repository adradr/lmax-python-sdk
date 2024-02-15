import typing
from .. import client


class LMAXMarketData(client.LMAXClient):
    def get_orderbook_snapshot(
        self,
        instrument_id: str,
        depth: int = 20,
    ) -> typing.Dict[str, typing.Any]:
        """
        Get current snapshot of the orderbook.

        This endpoint belongs to the "Market Data" rate limiting category and requires "Market Data" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - depth (int, optional): Depth of the order book. Defaults to 20.

        Returns:
        - typing.Dict[str, typing.Any]: The response from the LMAX API

        ```
                {
                    "instrument_id": "eur-usd",
                    "timestamp": "2022-01-01T12:12:12.123Z",
                    "status": "OPEN",
                    "bids": [
                        {
                            "price": "4.900000",
                            "quantity": "70000.0000"
                        }
                    ],
                    "asks": [
                        {
                            "price": "5.000000",
                            "quantity": "180000.0000"
                        }
                    ]
                }
        ```
        """
        endpoint = f"/v1/marketdata/{instrument_id}"
        params = {"depth": depth}
        return self._request(endpoint, params=params, authenticated=True)

    def historic_closing_prices(
        self,
        instrument_id: str,
        start_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
    ) -> typing.Dict[str, typing.Any]:
        """
        Gets the historical closing and settlement prices for an instrument, for a given date range. The maximum allowed date range is 1000 days.

        A start or an end date must be provided. If only the start date is given, then the date range will either be the next 1000 days from the start date, or from the start date till the current date if the resulting end date is in the future. Similarly, if only the end date is provided, then date range will either be the past 1000 days from the end date, or from 1st January 2010 till the end date if the resulting start date is before 2010. As we are only able to provide records from 2010 onwards.

        No prices are calculated for non-trading days. So, if no data is returned for a given date, then it means that date fell on a non-trading day and hence there is no closing price for that day. However, if just the closing date is returned without any prices, it means that for one reason or another, no prices were recorded for that day.

        This endpoint belongs to the "Query" rate limiting category and requires "Account Information" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - start_date (typing.Optional[str], Data in the format "YYYY-MM-DD", optional. Defaults to None.
        - end_date (typing.Optional[str], optional): Data in the format "YYYY-MM-DD", optional. Defaults to None.

        Returns:
        - typing.Dict[str, typing.Any]: The response from the LMAX API

        ```
                {
                    "instrument_id": "eur-usd",
                    "closing_prices": [
                        {
                            "closing_date": "2021-09-27",
                            "closing_price": "11.600000",
                            "settlement_price": "11.600000"
                        },
                        {
                            "closing_date": "2021-09-24",
                            "closing_price": "14.200000"
                        },
                        {
                            "closing_date": "2021-09-23",
                            "closing_price": "12.500000"
                        },
                        {
                            "closing_date": "2021-09-22"
                        }
                    ]
                }
        ```
        """
        endpoint = f"/v1/marketdata/{instrument_id}/historic-closing-prices"
        payload = {}
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        return self._request(endpoint, params=payload, authenticated=True)
