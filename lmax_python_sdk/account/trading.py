import typing
from .. import client
from ..validation import (
    OrderPlacementError,
    OrderTypeLiteral,
    SideTypeLiteral,
    TriggerMethodLiteral,
    TimeInForceLiteral,
    validate_order_type,
    validate_side_type,
    validate_trigger_method,
    validate_time_in_force,
    validate_id_length,
)


class LMAXTrading(client.LMAXClient):
    @validate_order_type
    @validate_side_type
    @validate_trigger_method
    @validate_time_in_force
    @validate_id_length("instruction_id")
    @validate_id_length("take_profit_instruction_id")
    @validate_id_length("stop_loss_instruction_id")
    def place_order(
        self,
        instrument_id: str,
        type: OrderTypeLiteral,  # pylint: disable=redefined-builtin
        side: SideTypeLiteral,
        quantity: str,
        instruction_id: str,
        time_in_force: TimeInForceLiteral,
        price: typing.Optional[str] = None,
        stop_price: typing.Optional[str] = None,
        trigger_method: typing.Optional[TriggerMethodLiteral] = None,
        take_profit_offset: typing.Optional[str] = None,
        take_profit_instruction_id: typing.Optional[str] = None,
        stop_loss_offset: typing.Optional[str] = None,
        stop_loss_instruction_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, str]:
        """Place order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - type (Order_Type): Order type, Enum: "MARKET" "LIMIT" "STOP" "STOP_LIMIT"
        - side (Side_Type): Side type, Enum: "BID" "ASK"
        - quantity (str): Quantity in base currency or other unit of measure (e.g. barrels, troy oz)
        - price (str): Limit price. Required for "LIMIT" and "STOP_LIMIT" orders
        - instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - time_in_force (Time_In_Force): Time in force of the order.
            - "FILL_OR_KILL" The order must totally fill or it is cancelled. Applicable to "LIMIT", "MARKET" orders.
            - "IMMEDIATE_OR_CANCEL" The order can either totally or partially fill, any remainder is cancelled. Applicable to "LIMIT", "MARKET" orders.
            - "GOOD_FOR_DAY" The order will try to fill what it can immediately, any remaining will rest on the orderbook. It will be cancelled at the end of the trading day.Applicable to "LIMIT", "STOP", "STOP_LIMIT" orders.
            - "GOOD_TIL_CANCELLED" The order will try to fill what it can immediately, any remaining will rest on the orderbook. It will not cancel at the end of trading day and will be placed the next day (and so on until you cancel it specifically). Applicable to "LIMIT", "STOP", "STOP_LIMIT" orders.
            - Enum: "FILL_OR_KILL" "IMMEDIATE_OR_CANCEL" "GOOD_FOR_DAY" "GOOD_TIL_CANCELLED"
        - stop_price (str): Stop price. Required for "STOP" and "STOP_LIMIT" orders
        - trigger_method (Trigger_Method): The method to trigger a "STOP" or "STOP_LIMIT" order and stop loss contingent orders.
            - "ONE_TOUCH" "ASK" orders trigger when the best bid price moves down to the stop_price (or below)
            - "ONE_TOUCH" "BID" orders trigger when the best ask price moves up to the stop_price (or above)
            - "BID_OFFER" "ASK" orders trigger when the best ask price moves down to the stop_price (or below)
            - "BID_OFFER" "BID" orders trigger when the best bid price moves up to the stop_price (or above)
            - Enum: "ONE_TOUCH" "BID_OFFER"
        - take_profit_offset (str): Stop offset from contingent order reference price; required when setting a take profit contingent order
        - take_profit_instruction_id (str): An identifier for this request's take profit order. Use ASCII characters from 33 to 126. Cannot be "0"; required when setting a take profit contingent order. Length must be less than 20 characters.
        - stop_loss_offset (str): Stop offset from contingent order reference price; required when setting a stop loss contingent order
        - stop_loss_instruction_id (str): An identifier for this request's stop loss order. Use ASCII characters from 33 to 126. Cannot be "0"; required when setting a stop loss contingent order. Length must be less than 20 characters.


        Returns:
        - typing.Dict[str, str]: The order details

        ```
                {
                    "order_type": "MARKET",
                    "account_id": "1653445",
                    "order_id": "VkZgzAAAAAJUC+QB",
                    "instruction_id": "instruction-1254",
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "quantity": "120000.0000",
                    "unfilled_quantity": "0.0000",
                    "matched_quantity": "80000.0000",
                    "cumulative_matched_quantity": "80000.0000",
                    "cancelled_quantity": "40000.0000",
                    "matched_cost": "120000.00000",
                    "commission": "180.00000",
                    "time_in_force": "IMMEDIATE_OR_CANCEL",
                    "side": "BID"
                }
        ```
        """
        endpoint = "/v1/account/place-order"
        if instruction_id == "0" or len(instruction_id) > 20:
            raise OrderPlacementError("Invalid instruction_id")

        if type in {"LIMIT", "STOP_LIMIT"} and not price:
            raise OrderPlacementError(
                "Price is required for LIMIT and STOP_LIMIT orders"
            )

        if type in {"STOP", "STOP_LIMIT"} and not stop_price:
            raise OrderPlacementError(
                "Stop price is required for STOP and STOP_LIMIT orders"
            )

        if (take_profit_offset or take_profit_instruction_id) and (
            not take_profit_offset or not take_profit_instruction_id
        ):
            raise OrderPlacementError(
                "Both take_profit_offset and take_profit_instruction_id are required for take profit orders"
            )

        if (stop_loss_offset or stop_loss_instruction_id) and (
            not stop_loss_offset or not stop_loss_instruction_id
        ):
            raise OrderPlacementError(
                "Both stop_loss_offset and stop_loss_instruction_id are required for stop loss orders"
            )

        # Check required fields
        if not instrument_id:
            raise OrderPlacementError("Instrument ID is required")
        if not type:
            raise OrderPlacementError("Order type is required")
        if not side:
            raise OrderPlacementError("Order side is required")
        if not quantity:
            raise OrderPlacementError("Quantity is required")
        if not instruction_id:
            raise OrderPlacementError("Instruction ID is required")
        if not time_in_force:
            raise OrderPlacementError("Time in force is required")

        # Construct the payload based on validated input
        payload = {
            "instrument_id": instrument_id,
            "type": type,
            "side": side,
            "quantity": str(quantity),
            "instruction_id": instruction_id,
            "time_in_force": time_in_force,
        }

        if price is not None:
            payload["price"] = str(price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)
        if trigger_method is not None:
            payload["trigger_method"] = trigger_method
        if take_profit_offset is not None:
            payload["take_profit_offset"] = str(take_profit_offset)
        if take_profit_instruction_id is not None:
            payload["take_profit_instruction_id"] = take_profit_instruction_id
        if stop_loss_offset is not None:
            payload["stop_loss_offset"] = str(stop_loss_offset)
        if stop_loss_instruction_id is not None:
            payload["stop_loss_instruction_id"] = stop_loss_instruction_id

        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_id_length("instruction_id")
    @validate_id_length("cancel_instruction_id")
    def cancel_order(
        self,
        instrument_id: str,
        cancel_instruction_id: str,
        instruction_id: str,
    ) -> typing.Dict[str, str]:
        """
        Cancel order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.


        Args:
        - instrument_id (str): Instrument identifier
        - cancel_instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - instruction_id (str): Instruction Id for the order to cancel. Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, str]: The order details

        ```
                {
                    "cancel_instruction_id": "cancel",
                    "order_type": "LIMIT",
                    "account_id": "1653445",
                    "order_id": "VkZgzAAAAAJUC+QB",
                    "instruction_id": "instruction-1254",
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "limit_price": "5.000000",
                    "quantity": "70000.0000",
                    "unfilled_quantity": "0.0000",
                    "matched_quantity": "30000.0000",
                    "cumulative_matched_quantity": "30000.0000",
                    "cancelled_quantity": "40000.0000",
                    "matched_cost": "150000.00000",
                    "commission": "5.25000",
                    "time_in_force": "GOOD_FOR_DAY",
                    "side": "BID"
                }
        ```
        """
        endpoint = "/v1/account/cancel-order"
        payload = {
            "instrument_id": instrument_id,
            "cancel_instruction_id": cancel_instruction_id,
            "instruction_id": instruction_id,
        }
        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_side_type
    @validate_id_length("replacement_instruction_id")
    @validate_id_length("instruction_id")
    def cancel_and_replace_order(
        self,
        instrument_id: str,
        replacement_instruction_id: str,
        instruction_id: str,
        side: SideTypeLiteral,
        quantity: str,
        price: str,
    ) -> typing.Dict[str, str]:
        """Cancel and replace order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - replacement_instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - instruction_id (str): Instruction Id for the order to cancel. Length must be less than 20 characters.
        - side (Side_Type): The side of the order. Bid is a buy. Ask is a sell, Enum: "BID" "ASK"
        - quantity (str): Quantity in base currency or other unit of measure (e.g. barrels, troy oz)
        - price (str): Limit price. Required for "LIMIT" and "STOP_LIMIT" orders

        Returns:
        - typing.Dict[str, str]: The order details

        ```
                {
                    "order_type": "LIMIT",
                    "account_id": "1653445",
                    "order_id": "VkZgzAAAAAJUC+QB",
                    "instruction_id": "instruction-1255",
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "limit_price": "5.000000",
                    "quantity": "120000.0000",
                    "unfilled_quantity": "90000.0000",
                    "matched_quantity": "0.0000",
                    "cumulative_matched_quantity": "30000.0000",
                    "cancelled_quantity": "0.0000",
                    "matched_cost": "0.00000",
                    "commission": "0.00000",
                    "time_in_force": "GOOD_FOR_DAY",
                    "side": "BID",
                    "replaced_instruction_id": "instruction-1254",
                }
        ```
        """
        endpoint = "/v1/account/cancel-and-replace-order"
        payload = {
            "instrument_id": instrument_id,
            "replacement_instruction_id": replacement_instruction_id,
            "instruction_id": instruction_id,
            "side": side,
            "quantity": str(quantity),
            "price": str(price),
        }
        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_id_length("cancel_instruction_id")
    def cancel_all_orders(
        self,
        cancel_instruction_id: str,
    ) -> typing.Dict[str, typing.Union[str, typing.List[typing.Dict[str, str]]]]:
        """
        Cancel all orders for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - cancel_instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, typing.Union[str, typing.List[typing.Dict[str, str]]]: The order details

        ```
                {
                    "account_id": "1653445",
                    "instruction_id": "cancel-all",
                    "cancelled_orders": [
                        {
                            "cancel_instruction_id": "cancel-all",
                            "order_type": "LIMIT",
                            "account_id": "1653445",
                            "order_id": "VkZgzAAAAAJUC+QB",
                            "instruction_id": "instruction-1254",
                            "instrument_id": "eur-usd",
                            "timestamp": "2024-01-21T22:24:55.874Z",
                            "limit_price": "5.000000",
                            "quantity": "70000.0000",
                            "unfilled_quantity": "0.0000",
                            "matched_quantity": "30000.0000",
                            "cumulative_matched_quantity": "30000.0000",
                            "cancelled_quantity": "40000.0000",
                            "matched_cost": "150000.00000",
                            "commission": "5.25000",
                            "time_in_force": "GOOD_FOR_DAY",
                            "side": "BID",
                        },
                        {
                            "cancel_instruction_id": "cancel-all",
                            "order_type": "LIMIT",
                            "account_id": "1653445",
                            "order_id": "FWaWswAAAAJUC+QB",
                            "instruction_id": "instruction-1255",
                            "instrument_id": "eur-usd",
                            "timestamp": "2024-01-21T22:29:55.874Z",
                            "limit_price": "4.900000",
                            "quantity": "180000.0000",
                            "unfilled_quantity": "0.0000",
                            "matched_quantity": "0.0000",
                            "cumulative_matched_quantity": "0.0000",
                            "cancelled_quantity": "180000.0000",
                            "matched_cost": "0.00000",
                            "commission": "0.00000",
                            "time_in_force": "GOOD_FOR_DAY",
                            "side": "BID",
                        },
                    ],
                }
        ```
        """
        endpoint = "/v1/account/cancel-all-orders"
        payload = {"cancel_instruction_id": cancel_instruction_id}
        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_side_type
    @validate_id_length("closing_instruction_id")
    @validate_id_length("instruction_id")
    def close_order(
        self,
        instrument_id: str,
        closing_instruction_id: str,
        side: SideTypeLiteral,
        quantity: str,
        instruction_id: typing.Optional[str] = None,
    ) -> typing.Dict[str, str]:
        """
        Close order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        To close an instrument position, do not specify instruction id.

        Args:
        - instrument_id (str): Instrument identifier
        - closing_instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - side (Side_Type): The side of the order. Bid is a buy. Ask is a sell, Enum: "BID" "ASK"
        - quantity (str): Quantity in base currency or other unit of measure (e.g. barrels, troy oz)
        - instruction_id (typing.Optional[str]): Instruction Id for the order to close. Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, str]: The order details

        ```
                {
                    "closed_instruction_id": "instruction-1254",
                    "order_type": "MARKET",
                    "account_id": "1653445",
                    "order_id": "VkZgzAAAAAJUC+QB",
                    "instruction_id": "closeinstruction-1",
                    "instrument_id": "eur-usd",
                    "timestamp": "2024-01-21T22:24:55.874Z",
                    "quantity": "80000.0000",
                    "unfilled_quantity": "0.0000",
                    "matched_quantity": "80000.0000",
                    "cumulative_matched_quantity": "80000.0000",
                    "cancelled_quantity": "0.0000",
                    "matched_cost": "-88000.00000",
                    "commission": "3.08000",
                    "time_in_force": "IMMEDIATE_OR_CANCEL",
                    "side": "ASK",
                }
        ```

        """
        endpoint = "/v1/account/close-order"
        payload = {
            "instrument_id": instrument_id,
            "closing_instruction_id": closing_instruction_id,
            "side": side,
            "quantity": str(quantity),
        }
        if instruction_id is not None:
            payload["instruction_id"] = instruction_id
        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_id_length("instruction_id")
    @validate_id_length("closing_instruction_id")
    def amend_take_profit(
        self,
        instrument_id: str,
        instruction_id: str,
        take_profit_offset: str,
        take_profit_instruction_id: str,
    ) -> typing.Dict[str, str]:
        """
        Amend take profit for an order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - take_profit_offset (str): Stop offset from contingent order reference price; required when setting a take profit contingent order
        - take_profit_instruction_id (str): An identifier for this request's take profit order. Use ASCII characters from 33 to 126. Cannot be "0"; required when setting a take profit contingent order. Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, str]: The order details

        ```
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
                    "take_profit_instruction_id": "tp-instruction-1254",
                    "take_profit_offset": "5.000000",
                    "contingent_order_reference_price": "5.000000",
                    "time_in_force": "GOOD_FOR_DAY",
                    "side": "BID",
                }
        ```

        """
        endpoint = "/v1/account/amend-take-profit"
        payload = {
            "instrument_id": instrument_id,
            "instruction_id": instruction_id,
            "take_profit_offset": str(take_profit_offset),
            "take_profit_instruction_id": take_profit_instruction_id,
        }
        return self._request(endpoint, "PUT", payload=payload, authenticated=True)

    @validate_id_length("instruction_id")
    def remove_take_profit(
        self,
        instrument_id: str,
        instruction_id: str,
    ) -> typing.Dict[str, str]:
        """
        Remove take profit for an order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, str]: The order details

        ```
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
                }
        ```

        """
        endpoint = "/v1/account/remove-take-profit"
        payload = {"instrument_id": instrument_id, "instruction_id": instruction_id}
        return self._request(endpoint, "POST", payload=payload, authenticated=True)

    @validate_id_length("instruction_id")
    def amend_stop_loss(
        self,
        instrument_id: str,
        instruction_id: str,
        stop_loss_offset: str,
        stop_loss_instruction_id: str,
        trigger_method: TriggerMethodLiteral,
    ) -> typing.Dict[str, str]:
        """
        Amend stop loss for an order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.
        - stop_loss_offset (str): Stop offset from contingent order reference price; required when setting a stop loss contingent order
        - stop_loss_instruction_id (str): An identifier for this request's stop loss order. Use ASCII characters from 33 to 126. Cannot be "0"; required when setting a stop loss contingent order. Length must be less than 20 characters.
        - trigger_method (Trigger_Method): The method to trigger a "STOP" or "STOP_LIMIT" order and stop loss contingent orders.
            - "ONE_TOUCH" "ASK" orders trigger when the best bid price moves down to the stop_price (or below)
            - "ONE_TOUCH" "BID" orders trigger when the best ask price moves up to the stop_price (or above)
            - "BID_OFFER" "ASK" orders trigger when the best ask price moves down to the stop_price (or below)
            - "BID_OFFER" "BID" orders trigger when the best bid price moves up to the stop_price (or above)
            - Enum: "ONE_TOUCH" "BID_OFFER"

        Returns:
        - typing.Dict[str, str]: The order details

        ```
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
                    "stop_loss_instruction_id": "sl-instruction-1254",
                    "stop_loss_offset": "5.000000",
                    "contingent_order_reference_price": "5.000000",
                    "time_in_force": "GOOD_FOR_DAY",
                    "side": "BID",
                }
        ```

        """
        endpoint = "/v1/account/amend-stop-loss"
        payload = {
            "instrument_id": instrument_id,
            "instruction_id": instruction_id,
            "stop_loss_offset": str(stop_loss_offset),
            "stop_loss_instruction_id": stop_loss_instruction_id,
            "trigger_method": trigger_method,
        }
        return self._request(endpoint, "PUT", payload=payload, authenticated=True)

    @validate_id_length("instruction_id")
    def remove_stop_loss(
        self,
        instrument_id: str,
        instruction_id: str,
    ) -> typing.Dict[str, str]:
        """
        Remove stop loss for an order for this account. This endpoint belongs to the "Trading" rate limiting category and requires "Trading" scope.

        Args:
        - instrument_id (str): Instrument identifier
        - instruction_id (str): An identifier for this request. Use ASCII characters from 33 to 126. Cannot be "0". Length must be less than 20 characters.

        Returns:
        - typing.Dict[str, str]: The order details

        ```
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
                }
        ```
        """
        endpoint = "/v1/account/remove-stop-loss"
        payload = {"instrument_id": instrument_id, "instruction_id": instruction_id}
        return self._request(endpoint, "POST", payload=payload, authenticated=True)
