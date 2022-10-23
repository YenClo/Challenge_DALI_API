# Author: Yunquan (Clooney) Gu
import asyncio
from collections import Counter, OrderedDict

import tweepy
from loguru import logger
from pycoingecko import CoinGeckoAPI

from app.config import GlobalConfig


class Twitter:
    def __init__(self, count=100):
        self.cg = CoinGeckoAPI()
        self.coin_list = self.cg.get_coins_list()
        self.api = tweepy.API(
            tweepy.AppAuthHandler(GlobalConfig.API_KEY,
                                  GlobalConfig.API_KEY_SECRET),
            wait_on_rate_limit=True)
        self.since_id = None
        self.count = count
        self.info = OrderedDict()
        self.text = "Not prepared"

    async def acquire_hot_coins_list(self):
        logger.info("Parsing data from twitter")
        count = 0
        hot_coin_set = Counter()

        # Keep searching until reach the set count
        while count < self.count:
            result = self.api.search_tweets(q=' OR '.join(GlobalConfig.COIN_QUERY) + '-filter:retweets',
                                            lang='en',
                                            result_type='recent',
                                            count=100,
                                            since_id=self.since_id)
            # since_id in search api means search twitters start from 'since_id'
            # so we need to set the since_id as the max_id from the last result
            self.since_id = result.max_id

            count += len(result)
            for tw in result:
                hot_coin_set.update(GlobalConfig.COIN_PATTERN.findall(tw.text))

                # Sometime, the coins hide in hashtags
                for hashtag in tw.entities['hashtags']:
                    hot_coin_set[hashtag['text']] += 1
        # Filter
        for k in list(hot_coin_set.keys()):
            if 'nft' in k or k in GlobalConfig.COIN_FILTER:
                del hot_coin_set[k]
        hot_coin_set = [k for k, v in hot_coin_set.most_common(30)]
        logger.info(f"update hot_coin_set: {hot_coin_set}")

        await asyncio.gather(*[self._lookup_coins(c) for c in hot_coin_set])
        logger.info(self.info)
        self.text = '\n'.join([
            f"Symbol: ${str(c):<30}\t\t"
            f"Current_price: ${self.info[c]['market_data-current_price']:.10f}\t\t"
            f"Price_change_24h: ${self.info[c]['market_data-price_change_24h']:.10f}\t\t"
            f"Price_change_percentage_24h: {self.info[c]['market_data-price_change_percentage_24h']}."
            for c in self.info
        ])
        logger.info(self.text)

    async def _lookup_coins(self, coin: str):
        # Look up coin information by coingecko api
        # There may be coins with the same name, just grab the one with the biggest volume

        coin_name = coin.strip("$").lower()
        target_coin, volume = None, -1

        for coin in self.coin_list:

            # coin name can be in 'name' 'symbol' and 'id' field
            if coin_name in [coin['name'], coin['symbol'], coin['id']]:
                try:
                    info = self.cg.get_coin_by_id(coin['id'])
                    if info['market_data']['total_volume']['usd'] > volume:
                        volume = info['market_data']['total_volume']['usd']
                        target_coin = info
                except Exception as e:
                    logger.exception(e)

        # Update the database, even if the coin already in the database
        if target_coin:
            logger.info(f'Add coin {target_coin["id"]}')
            self.update_coin(target_coin)
        else:
            logger.error(f"Failed to find coin {coin_name}")

    def update_coin(self, target_coin):
        logger.info(f'update {target_coin["id"]}')
        body = {}

        _id = body['id'] = target_coin['id']
        body['symbol'] = target_coin['symbol']
        body['name'] = target_coin['name']
        body['categories'] = target_coin["categories"]

        # Retrieve the platform of the coin(only one)
        for key in target_coin['platforms']:
            if key:
                body['platforms'] = key
                body['address'] = target_coin['platforms'][key]
                break

        # Retrieve the icon of the coin(three size)
        for size in target_coin['image']:
            body[f'image-{size}'] = target_coin['image'][size]

        # Retrieve the website of the coin
        for webpage in target_coin['links']:
            if isinstance(target_coin['links'][webpage], str):
                body[f'links-{webpage}'] = target_coin['links'][webpage]
            elif isinstance(target_coin['links'][webpage], list):
                body[f'links-{webpage}'] = target_coin['links'][webpage][0]

        # Retrieve the market data(1)
        for item in ['price_change_24h',
                     'price_change_percentage_24h',
                     'price_change_percentage_7d',
                     'price_change_percentage_14d',
                     'price_change_percentage_30d',
                     'price_change_percentage_60d',
                     'price_change_percentage_200d',
                     'market_cap_change_24h',
                     'market_cap_change_percentage_24h',
                     'market_cap_rank',
                     'total_supply',
                     'max_supply']:
            body[f'market_data-{item}'] = target_coin['market_data'].get(item, None)

        # Retrieve the market data(2)
        for item in ['current_price',
                     'high_24d',
                     'low_24d',
                     'market_cap',
                     'price_change_24h_in_currency',
                     'price_change_percentage_1h_in_currency',
                     'price_change_percentage_24h_in_currency',
                     'price_change_percentage_7d_in_currency',
                     'price_change_percentage_14d_in_currency',
                     'price_change_percentage_30d_in_currency',
                     'price_change_percentage_60d_in_currency',
                     'price_change_percentage_200d_in_currency',
                     'price_change_percentage_1y_in_currency',
                     'market_cap_change_24h_in_currency',
                     'market_cap_change_percentage_24h_in_currency']:
            body[f'market_data-{item}'] = target_coin['market_data'].get(item, {'usd': None}).get('usd', None)

        # Retrieve the public interest in sorting
        body['public_interest'] = target_coin['public_interest_score']

        if _id not in self.info and len(self.info) > 30:
            self.info.popitem(last=False)
        self.info[_id] = body
