from dataclasses import asdict, dataclass
import datetime
import enum
import os
import json
from time import sleep, time
from typing import Any, Generator, NamedTuple, Optional, Type
import requests

from kalshi.auth import KalshiAuth
from kalshi.constants import READ_LIMIT, WEBSOCKET_URL, WRITE_LIMIT, Endpoints
from websocket import WebSocketApp
import logging

from kalshi.types import GetEventsParams, GetMarketsParams, GetTradesParams, Market, Params, Response, Trade

_logger = logging.getLogger(__name__)




class KalshiBaseClient:
    def __init__(self):
        config = os.environ
        if config['MODE'] == 'PROD':
            key_id = config['PROD_KEY_ID']
            key_file = config['PROD_KEY_FILE']
            self.ws_base_url = config['PROD_WS_URL']
            self.base_url = config['PROD_BASE_URL']
        elif config['MODE'] == 'DEMO':
            key_id = config['DEMO_KEY_ID']
            key_file = config['DEMO_KEY_FILE']
            self.ws_base_url = config['DEMO_WS_URL']
            self.base_url = config['DEMO_BASE_URL']
        else:
            raise ValueError(f'Invalid mode in .env file: {config["MODE"]}')
        self.auth = KalshiAuth(key_id, key_file)


class KalshiHTTPClient(KalshiBaseClient):
    def __init__(self):
        super().__init__()
        self.next_write = None
        self.next_read = None

    def _get(self, path, params=None):
        _logger.info(f'GET {path} {params}')
        if self.next_read and time() < self.next_read:
            _logger.info(f'Sleeping for {self.next_read - time()}')
            sleep(self.next_read - time())
        url = self.base_url + path
        response = requests.get(url, params=params, auth=self.auth)
        response.raise_for_status()
        self.next_read = time() + READ_LIMIT
        return response.json()

    def _post(self, path, data=None):
        _logger.info(f'GET {path} {data}')
        if self.next_write and time() < self.next_write:
            sleep(self.next_write - time())
        url = self.base_url + path
        response = requests.post(url, json=data, auth=self.auth)
        response.raise_for_status()
        self.next_write = time() + WRITE_LIMIT
        return response

    def get_portfolio_balance(self) -> int:
        return self._get(Endpoints.PORTFOLIO.BALANCE)['balance']

    def get_trades(self, params: Optional[GetTradesParams] = None, **kwargs) -> Generator[Trade, None, None]:
        limit = kwargs.get('limit')
        api_limit = min(1000, limit) if limit else 1000
        yield from self._paginated_reponse(
            Endpoints.MARKET.TRADES,
            'trades',
            Trade,
            params,
            api_limit=api_limit,
            **kwargs,
        )
        

    def get_events(self, params: Optional[GetEventsParams] = None, **kwargs):
        limit = kwargs.get('limit')
        api_limit = min(200, limit) if limit else 200
        yield from self._paginated_reponse(
            Endpoints.MARKET.EVENTS,
            'events',
            params,
            api_limit=api_limit,
            **kwargs,
        )
    
    def get_event(self, event_id):
        return self._get(f'{Endpoints.MARKET.EVENTS}/{event_id}')
    
    def get_series(self, series_id):
        return self._get(f'{Endpoints.MARKET.SERIES}/{series_id}')

    def get_markets(
        self,
        params: Optional[GetMarketsParams] = None,
        **kwargs,
    ):
        limit = kwargs.get('limit')
        api_limit = min(200, limit) if limit else 200
        yield from self._paginated_reponse(
            Endpoints.MARKET.MARKETS,
            'markets',
            Market,
            params,
            api_limit=api_limit,
            **kwargs,
        )

    def get_market(
        self,
        market_id,
    ):
        return self._get(f'{Endpoints.MARKET.MARKETS}/{market_id}').market

    def _paginated_reponse[T: Response](
        self,
        path: str,
        key: str,
        response_type: Type[T],
        params: Optional[Params],
        api_limit: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Generator[T, None, None]:
        _params = params.to_dict() if params else {}
        if api_limit:
            _params['limit'] = api_limit
        if cursor:
            _params['cursor'] = cursor
        cursor = ''
        returned = 0
        while True:
            response = self._get(path, _params)
            _logger.info(f'Received {len(response[key])} Cursor: {response.get("cursor")}')
            for item in response[key]:
                yield response_type(**item)
                returned += 1
                if limit and returned >= limit:
                    return
            cursor = response.get('cursor', '')
            if not cursor:
                return
            _params['cursor'] = cursor


class KalshiWebSocketClient(KalshiBaseClient):
    """Client for handling WebSocket connections to the Kalshi API."""

    def __init__(self):
        super().__init__()
        self.ws = None
        self.message_id = 1  # Add counter for message IDs
        self.url_suffix = WEBSOCKET_URL

    def connect(self):
        """Establishes a WebSocket connection using authentication."""
        host = self.ws_base_url + self.url_suffix
        auth_headers = self.auth.get_headers('GET', self.url_suffix)
        header_list = [f'{k}: {v}' for k, v in auth_headers.items()]
        self.ws = WebSocketApp(
            host,
            header=header_list,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()

    def on_open(self, ws):
        """Callback when WebSocket connection is opened."""
        print('WebSocket connection opened.')
        self.subscribe_to_tickers()

    def subscribe_to_tickers(self):
        """Subscribe to ticker updates for all markets."""
        subscription_message = {
            'id': self.message_id,
            'cmd': 'subscribe',
            'params': {'channels': ['ticker']},
        }
        self.ws.send(json.dumps(subscription_message))
        self.message_id += 1

    def on_message(self, ws, message):
        """Callback for handling incoming messages."""
        print('Received message:', message)

    def on_error(self, ws, error):
        """Callback for handling errors."""
        print('WebSocket error:', error)

    def on_close(self, ws, close_status_code, close_msg):
        """Callback when WebSocket connection is closed."""
        print('WebSocket connection closed with code:', close_status_code)
