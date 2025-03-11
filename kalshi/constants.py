from typing import NamedTuple

WEBSOCKET_URL = '/trade-api/ws/v2'
READ_LIMIT = 1/10
WRITE_LIMIT = 1/10
class _PortfolioEndpoints(NamedTuple):
    BALANCE = '/portfolio/balance'

class _MarketEndpoints(NamedTuple):
    EVENTS = '/events'
    MARKETS = '/markets'
    TRADES = '/markets/trades'
    SERIES = '/series'

class Endpoints(NamedTuple):
    PORTFOLIO = _PortfolioEndpoints
    MARKET = _MarketEndpoints
