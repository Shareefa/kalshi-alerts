import datetime
import json
import os
import time
from dotenv import load_dotenv
import shlex
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from kalshi.client import KalshiHTTPClient, KalshiWebSocketClient
from kalshi.notification import TwilioClient
from kalshi.types import GetMarketsParams, GetTradesParams, Market, MarketStatus, Trade, GetEventsParams
from kalshi.utils import analyze_json_type
from dataclasses import asdict

_logger = logging.getLogger(__name__)


def get_markets(client: KalshiHTTPClient):
    params = GetMarketsParams(status=MarketStatus.OPEN)
    markets = list(client.get_markets(params))
    _logger.info(f'Got {len(markets)} markets')
    markets.sort(key=lambda x: x['volume_24h'], reverse=True)
    with open('./kalshi/data/markets.jsonl', 'w', encoding='utf-8') as f:
        f.writelines([json.dumps(market, ensure_ascii=False) + '\n' for market in markets])

def get_trades(client: KalshiHTTPClient, markets):
    start_date = datetime.datetime(2024,1,1)
    for market in markets[780:1000]:
        if '/' in market['ticker']:
            continue
        _logger.info(f'Getting trades for {market["ticker"]}')
        params = GetTradesParams(market['ticker'], min_ts=start_date)
        trades = client.get_trades(params)
        batch = []
        filename = shlex.quote(f'./kalshi/data/trades/{market["ticker"]}.jsonl')
        try:
            open(filename, 'a').close()
        except FileNotFoundError:
            continue

        nt = 0
        for trade in trades:
            nt += 1
            batch.append(trade)
            if len(batch) == 1000:
                with open(filename, 'a', encoding='utf-8') as f:
                    _logger.info(f'Writing Batch')
                    f.writelines([json.dumps(trade, ensure_ascii=False) + '\n' for trade in batch])
                    batch = []
        if batch:
            with open(filename, 'a', encoding='utf-8') as f:
                f.writelines([json.dumps(trade, ensure_ascii=False) + '\n' for trade in batch])
        _logger.info(f'Got {nt} trades for {market["ticker"]}')

def read_trades():
    for filename in os.listdir('./kalshi/data/trades'):
        with open(f'./kalshi/data/trades/{filename}', 'r', encoding='utf-8') as f:
            for line in f:
                yield json.loads(line)

def main():
    load_dotenv() 
    logging.basicConfig(level=logging.INFO)
    client = KalshiHTTPClient()

    with open('./data/kalshi_links.txt', 'r') as f:
        links = f.readlines()
    
    for link in links:
        link = link.strip()
        # Extract series ID from link format: https://kalshi.com/markets/{series_id}/...
        series_id = link.split('/markets/')[1].split('/')[0].upper()
        
        _logger.info(f'Getting series data for {series_id}')
        series_data = client.get_series(series_id)
        
        with open('./data/events.json', 'a', encoding='utf-8') as f:
            json.dump(series_data, f, indent=2, ensure_ascii=False)

    # get all markets for a series
    _logger.info('Getting all markets for a series')
    series_id = 'KXBTCD'
    params = GetMarketsParams(status=MarketStatus.OPEN, series_ticker=series_id)
    markets = client.get_markets(params=params, limit=10)
    for market in markets:
        with open('./data/markets_2.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(market), ensure_ascii=False, indent=2) + '\n')
    

if __name__ == '__main__':
    main()