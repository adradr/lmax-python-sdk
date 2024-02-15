import datetime
import typing
from .. import client
from ..validation import (
    validate_transaction_categories,
    validate_page_size,
    validate_after_before,
    validate_start_end_time,
    validate_id_length,
    TransactionCategoryLiteral,
)


class LMAXAccount(client.LMAXClient):

    def get_instrument_data(self) -> typing.Dict[str, typing.Union[str, list]]:
        """
        Fetches instrument data including funding, commission, margin rates, and account position limits.

        This endpoint belongs to the "query" rate limiting category and requires the "Account Information" scope.

        Returns: A dictionary containing instrument data with the following structure:

            ```
            {
                "account_id": "1653445",
                "timestamp": "2024-01-21T22:24:55.874Z",
                "instruments": [
                    {
                        "instrument_id": "eur-usd",
                        "security_id": "4001",
                        "symbol": "EUR/USD",
                        "currency": "USD",
                        "unit_of_measure": "EUR",
                        "quantity_increment": "1000.0000",
                        "margin": "2.00",
                        "minimum_position_size": "1000.0000",
                        "maximum_position_size": "1500000.0000",
                        "trading_days": [
                            "MONDAY",
                            "TUESDAY",
                            "WEDNESDAY",
                            "THURSDAY",
                            "FRIDAY",
                            "SATURDAY",
                            "SUNDAY"
                        ],
                        "open_time": "17:05",
                        "close_time": "17:00",
                        "time_zone": "America/New_York",
                        "minimum_commission": "10.00000",
                        "aggressive_commission_rate": "0.25000",
                        "passive_commission_rate": "0.13000",
                        "price_increment": "0.000010",
                        "minimum_price": "0.000000",
                        "maximum_price": "99999.000000",
                        "short_swap_points": "1.129",
                        "long_swap_points": "1.119",
                        "short_swap_cost": "1.12900",
                        "long_swap_cost": "-1.11900",
                        "swap_cost_units": "10000.0000",
                        "trade_date": "2023-10-11",
                        "value_date_from": "2023-10-13",
                        "value_date_to": "2023-10-14",
                        "asset_class": "CURRENCY"
                    },
                    {
                        "instrument_id": "eur-usd",
                        "security_id": "4001",
                        "symbol": "EUR/USD",
                        "currency": "USD",
                        "unit_of_measure": "EUR",
                        "quantity_increment": "1000.0000",
                        "margin": "2.00",
                        "minimum_position_size": "1000.0000",
                        "maximum_position_size": "1500000.0000",
                        "trading_days": [
                            "MONDAY",
                            "TUESDAY",
                            "WEDNESDAY",
                            "THURSDAY",
                            "FRIDAY",
                            "SATURDAY",
                            "SUNDAY"
                        ],
                        "open_time": "17:05",
                        "close_time": "17:00",
                        "time_zone": "America/New_York",
                        "minimum_commission": "10.00000",
                        "aggressive_commission_rate": "0.25000",
                        "passive_commission_rate": "0.13000",
                        "price_increment": "0.000010",
                        "minimum_price": "0.000000",
                        "maximum_price": "99999.000000",
                        "long_financing_rate": "0.02",
                        "short_financing_rate": "0.03",
                        "funding_base_rate": "LIBOR",
                        "asset_class": "INDEX"
                    }
                ]
            }
            ```
        """
        endpoint = "/v1/account/instrument-data"
        return self._request(endpoint, method="GET", authenticated=True)

    def get_instrument_data_symbol(self, symbol: str) -> typing.List[dict]:
        """Fetches instrument data for a specific symbol by filtering the instruments list.

        Args:
        - symbol (str): The symbol to filter the instruments list. You can get the list of symbols from the `symbols` attribute.

        Returns:
        - typing.List[dict]: A list of instruments with the specified symbol.
        """
        endpoint = "/v1/account/instrument-data"
        instruments = self._request(endpoint, method="GET", authenticated=True)
        return [
            instrument
            for instrument in instruments["instruments"]
            if instrument["symbol"] == symbol
        ]

    @validate_id_length("instruction_id")
    def get_order_state(
        self,
        instruction_id: typing.Optional[str] = None,
        order_id: typing.Optional[str] = None,
        instrument_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, str]:
        """
        Fetch an order state from the last seven days. The order can be queried by either URL-encoded 'Order Id' or the combination of URL-encoded 'Instruction Id' and 'Instrument Id'.

        This endpoint belongs to the "Account" rate limiting category and requires "Account Information" scope.

        Args:
        - instruction_id (str, optional): Instruction Id, may contain RFC3986 reserved characters and should be URL encoded. Defaults to None. Example: instruction_id=instruction-1254
        - order_id (str, optional): Order Id, may contain RFC3986 reserved characters and should be URL encoded.. Defaults to None. Example: order_id=VkZgzAAAAAJUC%2BQB
        - instrument_id (str, optional): Instrument Id. Defaults to None. Example: instrument_id=eur-usd

        Returns:
        - typing.Dict[str, str]: A dictionary containing the order state.

            ```
                {
                    "account_id": "1653445",
                    "order_id": "FWaWswAAAAJUC+QB",
                    "instruction_id": "instruction-1255",
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-01-21T22:29:55.874Z",
                    "limit_price": "1.500000",
                    "quantity": "120000.0000",
                    "unfilled_quantity": "40000.0000",
                    "matched_quantity": "80000.0000",
                    "cumulative_matched_quantity": "80000.0000",
                    "cancelled_quantity": "0.0000",
                    "matched_cost": "120000.00000",
                    "commission": "4.20000",
                    "time_in_force": "GOOD_FOR_DAY",
                    "side": "BID",
                    "order_status": "PARTIALLY_FILLED"
                    }
            ```

        Raises:
        - ValueError: If both instrument_id and order_id are provided.
        - ValueError: If neither instrument_id nor order_id are provided.
        """
        # "Both instrument_id and order_id are provided. Only one of them is allowed."
        if instrument_id and order_id:
            raise ValueError(
                "Both instrument_id and order_id are provided. Only one of them is allowed."
            )

        # "One of the following query parameters are required: instruction_id, order_id"}
        if not (instruction_id or order_id):
            raise ValueError(
                "One of the following query parameters is required: instruction_id or order_id"
            )

        # "Only one of the following query parameters are accepted: instruction_id, order_id"
        if instruction_id and order_id:
            raise ValueError(
                "Only one of the following query parameters are accepted: instruction_id, order_id"
            )

        # Must supply instrument id with instruction id
        if instruction_id and not instrument_id:
            raise ValueError("Must supply instrument_id with instruction_id")

        endpoint = "/v1/account/order-state"
        params = {}
        if instruction_id:
            params["instruction_id"] = instruction_id
        if order_id:
            params["order_id"] = order_id
        if instrument_id:
            params["instrument_id"] = instrument_id

        endpoint += "?" + "&".join([f"{key}={value}" for key, value in params.items()])
        return self._request(endpoint, method="GET", params=params, authenticated=True)

    @validate_page_size
    @validate_after_before
    def get_working_orders(
        self,
        page_size: typing.Optional[int] = 1000,
        after: typing.Optional[str] = None,
        before: typing.Optional[str] = None,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """
        Fetch all unfilled orders for this account. This endpoint belongs to the "Account" rate limiting category and requires "Account Information" scope.

        This is a "paginated endpoint".

        Args:
        - page_size (int, optional): Maximum number of orders to be included into the response. Defaults to 1000.
        - after (str, optional): Fetch orders after this cursor (more recent). This parameter is incompatible with before. Defaults to None.
        - before (str, optional): Fetch orders before this cursor (earlier orders). This parameter is incompatible with after. Defaults to None.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[dict]]]: A dictionary containing the working orders.

            ```
                {
                    "before_cursor": "b8d3b51bd5b255857ef1c9164772efc759df2d61e33780c8f1e3593ec9e71cdad0f73851fa1863",
                    "after_cursor": "fd273b1600fbc3e1526dd0c32a8b92ccc18e43e54daaccc59eb491a361f05eb6c6328aa6e74343",
                    "orders": [
                        {
                        "account_id": "1653445",
                        "order_id": "VkZgzAAAAAJUC+QB",
                        "instruction_id": "instruction-1254",
                        "instrument_id": "eur-usd",
                        "timestamp": "2024-01-21T22:24:55.874Z",
                        "limit_price": "5.000000",
                        "quantity": "70000.0000",
                        "unfilled_quantity": "40000.0000",
                        "matched_quantity": "30000.0000",
                        "cumulative_matched_quantity": "30000.0000",
                        "cancelled_quantity": "0.0000",
                        "matched_cost": "150000.00000",
                        "commission": "5.25000",
                        "time_in_force": "GOOD_FOR_DAY",
                        "side": "BID",
                        "order_type": "LIMIT"
                        }
                    ]
                }
            ```
        """
        endpoint = "/v1/account/working-orders"
        params = {"page_size": page_size, "after": after, "before": before}
        return self._request(endpoint, method="GET", params=params, authenticated=True)

    @validate_page_size
    @validate_after_before
    def get_order_positions(
        self,
        page_size: typing.Optional[int] = 1000,
        after: typing.Optional[str] = None,
        before: typing.Optional[str] = None,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """
        Fetch order positions.

        This endpoint belongs to the "Account" rate limiting category and requires "Account Information" scope.

        This is a "paginated endpoint".

        Args:
        - page_size (int, optional): Maximum number of orders to be included into the response. Defaults to 1000.
        - after (str, optional): Fetch orders after this cursor (more recent). This parameter is incompatible with before. Defaults to None.
        - before (str, optional): Fetch orders before this cursor (earlier orders). This parameter is incompatible with after. Defaults to None.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[dict]]]: Order positions.

            ```
                {
                    "before_cursor": "b8d3b51bd5b255857ef1c9164772efc759df2d61e33780c8f1e3593ec9e71cdad0f73851fa1863",
                    "after_cursor": "fd273b1600fbc3e1526dd0c32a8b92ccc18e43e54daaccc59eb491a361f05eb6c6328aa6e74343",
                    "positions": [
                        {
                            "account_id": "1653445",
                            "order_id": "FWaWswAAAAJUC+QB",
                            "instrument_id": "gbp-usd",
                            "instruction_id": "instruction-1254",
                            "open_quantity": "50000.0000",
                            "open_cost": "-250000.00000",
                            "side": "ASK",
                            "timestamp": "2024-01-21T22:24:55.874Z"
                        },
                        {
                            "account_id": "1653445",
                            "order_id": "VkZgzAAAAAJUC+QB",
                            "instrument_id": "eur-usd",
                            "instruction_id": "instruction-1255",
                            "open_quantity": "70000.0000",
                            "open_cost": "350000.00000",
                            "side": "BID",
                            "timestamp": "2024-01-21T22:29:55.874Z"
                        }
                    ]
                }
            ```
        """
        endpoint = "/v1/account/order-positions"
        params = {"page_size": page_size, "after": after, "before": before}
        return self._request(endpoint, method="GET", params=params, authenticated=True)

    def get_instrument_positions(
        self,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """
        Fetch account instrument positions.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[dict]]]: Account instrument positions.

            ```
                {
                    "positions": [
                        {
                            "account_id": "1653445",
                            "timestamp": "2024-01-21T22:24:55.874Z",
                            "instrument_id": "eur-usd",
                            "open_quantity": "30000.0000",
                            "open_cost": "150000.00000",
                            "unfilled_buy_quantity": "40000.0000",
                            "unfilled_buy_cost": "208000.00000",
                            "unfilled_sell_quantity": "0.0000",
                            "unfilled_sell_cost": "0.00000",
                            "currency": "USD",
                            "side": "BID"
                        }
                    ]
                }
            ```
        """
        endpoint = "/v1/account/positions"
        return self._request(endpoint, method="GET", authenticated=True)

    def get_wallet_balances(
        self,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """Fetch account wallet balances.

        This endpoint belongs to the "Account" rate limiting category and requires "Account Information" scope.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[dict]]]: Account wallet balances.

            ```
                {
                    "account_id": "1653445",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "wallets": [
                        {
                            "currency": "USD",
                            "cash": "1000000.00000",
                            "credit": "700.00000",
                            "balance": "1000700.00000"
                        }
                    ]
                }
            ```
        """
        endpoint = "/v1/account/wallets"
        return self._request(endpoint, method="GET", authenticated=True)

    def get_collaterized_credit(self) -> dict:
        """Total collateralized credit and how much has been used.

        Note that not all accounts support collateralized credit.

        Calling this endpoint for an unsupported account returns a not supported response.

        This endpoint belongs to the "Account" rate limiting category and requires "Account Information" scope.

        Returns:
        - dict: Total collateralized credit and how much has been used.

            ```
                {
                    "account_id": "1653445",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "currency": "USD",
                    "cash": "15000.00000",
                    "total_collateralized_credit": "20000.00000",
                    "used_collateralized_credit": "0.00000"
                }
            ```
        """
        endpoint = "/v1/account/collateralized-credit"
        return self._request(endpoint, method="GET", authenticated=True)

    @validate_start_end_time
    @validate_page_size
    @validate_after_before
    @validate_transaction_categories
    def get_transactions(
        self,
        start_time: typing.Optional[str] = None,
        end_time: typing.Optional[str] = None,
        page_size: typing.Optional[int] = 1000,
        after: typing.Optional[str] = None,
        before: typing.Optional[str] = None,
        transaction_categories: typing.Optional[TransactionCategoryLiteral] = None,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """
        Fetch account transactions.

        This endpoint belongs to the "Query" rate limiting category and requires "Account Information" scope.

        This is a "paginated endpoint.

        Parameters:
        - start_time (str): ISO8601 timestamp for the start time.
            - start_time=2021-09-11T08:00:00.000Z - ISO8601 timestamp with millisecond resolution
            - start_time=2021-09-11T08:00:00Z - ISO8601 timestamp with second resolution
        - end_time (str): ISO8601 timestamp for the end time.
            - end_time=2021-09-12T08:00:00.000Z - ISO8601 timestamp with millisecond resolution
            - end_time=2021-09-12T08:00:00Z - ISO8601 timestamp with second resolution
        - page_size (int, optional): Maximum number of orders to be included into the response. Defaults to 1000. Must be within the range 1 to 1000.
        - after (str, optional): Fetch orders after this cursor (more recent). This parameter is incompatible with before. Defaults to None.
        - before (str, optional): Fetch orders before this cursor (earlier orders). This parameter is incompatible with after. Defaults to None.
        - transaction_categories (Optional[TransactionCategory]): Filter transactions by category.

        Returns:
        - dict: Account transactions.

            ```
                {
                    "before_cursor": "b8d3b51bd5b255857ef1c9164772efc759df2d61e33780c8f1e3593ec9e71cdad0f73851fa1863",
                    "after_cursor": "fd273b1600fbc3e1526dd0c32a8b92ccc18e43e54daaccc59eb491a361f05eb6c6328aa6e74343",
                    "status": "COMPLETED",
                    "transactions": [
                    {
                    "transaction_category": "EXECUTION",
                    "account_id": "1653445",
                    "account_statement_id": "6",
                    "amount": "15000.00000",
                    "currency_balance": "2014999.80000",
                    "currency": "USD",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "execution_type": "EXECUTION",
                    "trade_date": "2021-01-01",
                    "instrument_id": "eur-usd",
                    "execution_id": "ABk6xQAAAAAAADA5",
                    "quantity_closed": "50000.0000",
                    "opening_order_id": "VkZgzAAAAAJUC+QB",
                    "opening_price": "5.200000",
                    "closing_order_id": "FWaWswAAAAJUC+QB",
                    "closing_price": "5.500000",
                    "side": "ASK"
                    }]
                }
            ```

        Raises:
        - ValueError: If page_size is not within the range 1 to 1000.
        - ValueError: If transaction_categories is not a string.
        - ValueError: If transaction_categories is not one of the TransactionCategory enum.
        - ValueError: If start_time and end_time are not datetime objects.
        - ValueError: If both after and before are provided.
        """

        endpoint = "/v1/account/account-transactions"
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "after": after,
            "before": before,
            "transaction_categories": transaction_categories,
        }
        return self._request(endpoint, method="GET", params=params, authenticated=True)

    @validate_start_end_time
    @validate_page_size
    @validate_after_before
    def get_trade_history(
        self,
        start_time: typing.Optional[str] = None,
        end_time: typing.Optional[str] = None,
        page_size: typing.Optional[int] = 1000,
        after: typing.Optional[str] = None,
        before: typing.Optional[str] = None,
        order_information: bool = False,
    ) -> typing.Dict[str, typing.Union[str, typing.List[dict]]]:
        """
        Fetch account trades. When requesting before or after trades only one query parameter is allowed (before or after).

        This endpoint belongs to the "Query" rate limiting category and requires "Account Information" scope.

        This is a "paginated endpoint".

        Args:
        - start_time (str): ISO8601 timestamp for the start time.
            - start_time=2021-09-11T08:00:00.000Z - ISO8601 timestamp with millisecond resolution
            - start_time=2021-09-11T08:00:00Z - ISO8601 timestamp with second resolution
        - end_time (str): ISO8601 timestamp for the end time.
            - end_time=2021-09-12T08:00:00.000Z - ISO8601 timestamp with millisecond resolution
            - end_time=2021-09-12T08:00:00Z - ISO8601 timestamp with second resolution
        - page_size (int, optional): Maximum number of records to be returned at once. Defaults to 1000.
        - after (str, optional): Fetch trades after this cursor (more recent). This parameter is incompatible with before. Defaults to None.
        - before (str, optional): Fetch trades before this cursor (earlier trades). This parameter is incompatible with after. Defaults to None.
        - order_information (bool, optional): Whether to include order information in the response. Defaults to False.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[dict]]]: Dictionary containing the trade history.

            ```
                {
                    "before_cursor": "b8d3b51bd5b255857ef1c9164772efc759df2d61e33780c8f1e3593ec9e71cdad0f73851fa1863",
                    "after_cursor": "fd273b1600fbc3e1526dd0c32a8b92ccc18e43e54daaccc59eb491a361f05eb6c6328aa6e74343",
                    "trades": [
                        {
                        "account_id": "1653445",
                        "instrument_id": "gbp-usd",
                        "execution_id": "ABk6xQAAAAAAADA6",
                        "timestamp": "2024-01-21T22:24:55.874Z",
                        "price": "5.000000",
                        "quantity": "70000.0000",
                        "order_id": "FWaWswAAAAJUC+QB",
                        "side": "ASK",
                        "commission": "0.00000",
                        "order_information": {
                            "instruction_id": "instruction-1255",
                            "order_placement_timestamp": "2024-01-21T22:24:55.874Z",
                            "limit_price": "5.000000",
                            "order_type": "LIMIT",
                            "order_quantity": "70000.0000",
                            "order_status": "FILLED"
                        }
                        },
                        {
                        "account_id": "1653445",
                        "instrument_id": "eur-usd",
                        "execution_id": "ABk6xQAAAAAAADA5",
                        "timestamp": "2024-01-21T22:24:55.874Z",
                        "price": "5.000000",
                        "quantity": "50000.0000",
                        "order_id": "VkZgzAAAAAJUC+QB",
                        "side": "BID",
                        "commission": "8.75000",
                        "order_information": {
                            "instruction_id": "instruction-1254",
                            "order_placement_timestamp": "2024-01-21T22:24:55.874Z",
                            "order_type": "MARKET",
                            "order_quantity": "50000.0000",
                            "order_status": "FILLED"
                        }
                        }
                    ]
                    }
            ```
        """
        endpoint = "/v1/account/trades"
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "page_size": page_size,
            "after": after,
            "before": before,
            "order_information": order_information,
        }
        return self._request(endpoint, method="GET", params=params, authenticated=True)
