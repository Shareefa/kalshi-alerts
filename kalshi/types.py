
from dataclasses import asdict, dataclass
import datetime
import enum
from typing import Optional

from typing import Optional, Dict
import pydantic
from enum import Enum

@dataclass()
class Params():
    def to_dict(self):
        ret = {}
        for k, v in asdict(self).items():
            if isinstance(v, enum.Enum):
                ret[k] = v.value
            elif isinstance(v, list):
                ret[k] = ','.join(v)
            elif isinstance(v, datetime.datetime):
                ret[k] = int(v.timestamp())
            elif v is not None:
                ret[k] = v
        return ret



class MarketStatus(enum.Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    UNOPENED = 'unopened'
    SETTLED = 'settled'

@dataclass
class GetEventsParams(Params):
    series_ticker: Optional[str] = None
    event_ticker: Optional[str] = None
    status: Optional[str] = None
    with_nested_markets: bool = False

@dataclass
class GetEventParams(Params):
    event_ticker: Optional[str] = None
    with_nested_markets: bool = False

@dataclass
class GetMarketsParams(Params):
    event_ticker: Optional[str] = None
    series_ticker: Optional[str] = None
    status: Optional[MarketStatus] = None
    tickers: Optional[list[str]] = None
    max_close_ts: Optional[datetime.datetime] = None
    min_close_ts: Optional[datetime.datetime] = None
@dataclass
class GetTradesParams(Params):
    ticker: str
    min_ts: Optional[datetime.datetime] = None
    max_ts: Optional[datetime.datetime] = None

class Response:
    pass

@pydantic.dataclasses.dataclass
class Trade(Response):
    trade_id: str
    ticker: str
    count: int
    created_time: datetime.datetime
    yes_price: int
    no_price: int
    taker_side: str


class MarketType(str, Enum):
    BINARY = "binary"
    SCALAR = "scalar"

class MarketResult(str, Enum):
    YES = "yes"
    NO = "no"
    VOID = "void"
    ALL_NO = "all_no"
    ALL_YES = "all_yes"

class StrikeType(str, Enum):
    UNKNOWN = "unknown"
    GREATER = "greater"
    LESS = "less"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    BETWEEN = "between"
    FUNCTIONAL = "functional"
    CUSTOM = "custom"

# @pydantic.dataclasses.dataclass
@dataclass
class Market(Response):
    # Required fields
    can_close_early: bool
    category: str 
    close_time: datetime.datetime
    event_ticker: str
    expiration_time: datetime.datetime
    last_price: int
    latest_expiration_time: datetime.datetime
    liquidity: int
    market_type: MarketType
    no_ask: int
    no_bid: int
    no_sub_title: str
    notional_value: int
    open_interest: int
    open_time: datetime.datetime
    previous_price: int
    previous_yes_ask: int
    previous_yes_bid: int
    response_price_units: str
    risk_limit_cents: int
    rules_primary: str
    rules_secondary: str
    settlement_timer_seconds: int
    status: str
    tick_size: int
    ticker: str
    title: str
    volume: int
    volume_24h: int
    yes_ask: int
    yes_bid: int
    yes_sub_title: str

    # Optional fields
    cap_strike: Optional[float] = None
    custom_strike: Optional[Dict] = None
    expected_expiration_time: Optional[datetime.datetime] = None
    expiration_value: Optional[str] = None
    fee_waiver_expiration_time: Optional[datetime.datetime] = None
    floor_strike: Optional[float] = None
    functional_strike: Optional[str] = None
    result: Optional[MarketResult] = None
    settlement_value: Optional[int] = None
    subtitle: Optional[str] = None
    strike_type: Optional[StrikeType] = None

    @pydantic.field_validator('result', mode='before')
    def parse_empty_string_to_none(cls, value):
        if value == "":
            return None
        return value
