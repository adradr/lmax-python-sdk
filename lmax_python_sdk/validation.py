import enum
import typing
import pprint
import datetime
import functools


class TypeEnumMeta(enum.EnumMeta):
    def __getattribute__(cls, name):
        # Attempt to get the attribute normally
        member = super().__getattribute__(name)
        # If the member is an instance of an enum (checking for 'value' to make it more generic),
        # return the value directly
        if isinstance(member, enum.Enum) and hasattr(member, "value"):
            return member.value
        return member


class TypeEnum(enum.Enum, metaclass=TypeEnumMeta):
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def dict(cls):
        # Print key and value of the enum using pprint
        pprint.pprint({member.name: member.value for member in cls})


class ClientBaseURLType(TypeEnum):

    ACCOUNT_LONDON = "https://account-api.london.lmax.com"
    ACCOUNT_LONDON_PROFESSIONAL = "https://account-api.london-professional.lmax.com"
    ACCOUNT_LONDON_DEMO = "https://account-api.london-demo.lmax.com"
    ACCOUNT_LONDON_DIGITAL = "https://account-api.london-digital.lmax.com"
    ACCOUNT_LONDON_UAT = "https://account-api.london-uat.lmax.com"
    ACCOUNT_NEWYORK_PROFESSIONAL = "https://account-api.newyork-professional.lmax.com"
    ACCOUNT_TOKYO_PROFESSIONAL = "https://account-api.tokyo-professional.lmax.com"
    ACCOUNT_SINGAPORE_PROFESSIONAL = (
        "https://account-api.singapore-professional.lmax.com"
    )
    ACCOUNT_DIGITAL_UAT = "https://account-api.digital-uat.lmax.com"
    PUBLIC_DATA_LONDON_DEMO = "https://public-data-api.london-demo.lmax.com"
    PUBLIC_DATA_LONDON_DIGITAL = "https://public-data-api.london-digital.lmax.com"
    MARKET_DATA_LONDON_PROFESSIONAL = (
        "https://market-data-api.london-professional.lmax.com"
    )
    MARKET_DATA_LONDON_DIGITAL = "https://market-data-api.london-digital.lmax.com"
    MARKET_DATA_NEWYORK_PROFESSIONAL = (
        "https://market-data-api.newyork-professional.lmax.com"
    )
    MARKET_DATA_TOKYO_PROFESSIONAL = (
        "https://market-data-api.tokyo-professional.lmax.com"
    )
    MARKET_DATA_SINGAPORE_PROFESSIONAL = (
        "https://market-data-api.singapore-professional.lmax.com"
    )
    MARKET_DATA_LONDON_DEMO = "https://market-data-api.london-demo.lmax.com"
    MARKET_DATA_LONDON_UAT = "https://market-data-api.london-uat.lmax.com"
    MARKET_DATA_DIGITAL_UAT = "https://market-data-api.digital-uat.lmax.com"


class TransactionCategory(TypeEnum):
    BANK_TRANSFER_CURRENCY_CONVERSION = "BANK_TRANSFER_CURRENCY_CONVERSION"
    BASE_CURRENCY_SWEEP = "BASE_CURRENCY_SWEEP"
    COMMISSION = "COMMISSION"
    COMMISSION_REVENUE = "COMMISSION_REVENUE"
    DEBIT_CREDIT = "DEBIT_CREDIT"
    DELIVERABLE = "DELIVERABLE"
    DIVIDEND = "DIVIDEND"
    EXECUTION = "EXECUTION"
    FOREIGN_CURRENCY_SWEEP = "FOREIGN_CURRENCY_SWEEP"
    FUNDING = "FUNDING"
    FX_FUNDING = "FX_FUNDING"
    MARK_TO_MARKET_PROFIT_LOSS = "MARK_TO_MARKET_PROFIT_LOSS"


class OrderType(TypeEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"


class SideType(TypeEnum):
    BID = "BID"
    ASK = "ASK"


class TriggerMethodType(TypeEnum):
    ONE_TOUCH = "ONE_TOUCH"
    BID_OFFER = "BID_OFFER"


class TimeInForceType(TypeEnum):
    FILL_OR_KILL = "FILL_OR_KILL"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    GOOD_FOR_DAY = "GOOD_FOR_DAY"
    GOOD_TIL_CANCELLED = "GOOD_TIL_CANCELLED"


valid_client_base_urls = [base_url.value for base_url in ClientBaseURLType]
valid_transaction_categories = [category.value for category in TransactionCategory]
valid_order_types = [order_type.value for order_type in OrderType]
valid_side_types = [side_type.value for side_type in SideType]
valid_trigger_methods = [trigger_method.value for trigger_method in TriggerMethodType]
valid_time_in_forces = [time_in_force.value for time_in_force in TimeInForceType]


def get_literal_values(enum) -> typing.List[str]:
    return [e.value for e in enum]


BaseURLLiteral = typing.Literal[tuple(get_literal_values(ClientBaseURLType))]

TransactionCategoryLiteral = typing.Literal[
    tuple(get_literal_values(TransactionCategory))
]

OrderTypeLiteral = typing.Literal[tuple(get_literal_values(OrderType))]

SideTypeLiteral = typing.Literal[tuple(get_literal_values(SideType))]

TriggerMethodLiteral = typing.Literal[tuple(get_literal_values(TriggerMethodType))]

TimeInForceLiteral = typing.Literal[tuple(get_literal_values(TimeInForceType))]


class OrderPlacementError(Exception):
    pass


def validate_page_size(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        page_size = kwargs.get("page_size", 1000)
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000, inclusive.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_transaction_categories(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        transaction_categories = kwargs.get("transaction_categories")
        if transaction_categories is not None and not isinstance(
            transaction_categories, str
        ):
            raise ValueError("transaction_categories must be a string.")
        if (
            transaction_categories is not None
            and transaction_categories not in valid_transaction_categories
        ):
            raise ValueError(
                "transaction_categories must be one of the valid categories."
            )
        return func(self, *args, **kwargs)

    return wrapper


def validate_start_end_time(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = kwargs.get("start_time")
        end_time = kwargs.get("end_time")
        if start_time is not None and end_time is not None:
            if not all(
                [
                    isinstance(start_time, datetime.datetime),
                    isinstance(end_time, datetime.datetime),
                ]
            ):
                raise ValueError("start_time and end_time must be datetime objects.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_after_before(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        after = kwargs.get("after")
        before = kwargs.get("before")
        if not isinstance(after, str) and after:
            raise ValueError("after must be a string.")
        if not isinstance(before, str) and before:
            raise ValueError("before must be a string.")
        if after and before:
            raise ValueError("after and before cannot be provided together.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_order_type(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        order_type = kwargs.get("type")
        if not isinstance(order_type, str) and order_type is not None:
            raise ValueError("type must be a string or None.")
        if order_type not in valid_order_types and order_type is not None:
            raise ValueError("type must be one of the valid order types.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_side_type(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        side = kwargs.get("side")
        if not isinstance(side, str) and side is not None:
            raise ValueError("side must be a string or None.")
        if side not in valid_side_types and side is not None:
            raise ValueError("side must be one of the valid side types.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_trigger_method(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        trigger_method = kwargs.get("trigger_method")
        if not isinstance(trigger_method, str) and trigger_method is not None:
            raise ValueError("trigger_method must be a string or None.")
        if trigger_method not in valid_trigger_methods and trigger_method is not None:
            raise ValueError("trigger_method must be one of the valid trigger methods.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_time_in_force(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        time_in_force = kwargs.get("time_in_force")
        if not isinstance(time_in_force, str) and time_in_force is not None:
            raise ValueError("time_in_force must be a string or None.")
        if time_in_force not in valid_time_in_forces and time_in_force is not None:
            raise ValueError("time_in_force must be one of the valid time in forces.")
        return func(self, *args, **kwargs)

    return wrapper


def validate_id_length(id_arg):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            id_value = kwargs.get(id_arg)
            if not isinstance(id_value, str) and id_value is not None:
                raise ValueError(f"{id_arg} must be a string.")
            if id_value is not None:
                if len(id_value) >= 20:
                    raise ValueError(
                        f"{id_arg} must be less or equal to 20 characters."
                    )
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
