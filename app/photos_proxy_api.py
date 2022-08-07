import json
import pickle

import aiohttp
import aioredis

from app.models import Photo


class PhotosProxyApi:
    URL_API_PHOTOS = 'https://api.unsplash.com/photos'
    HEADEARS = {
        'Authorization': 'Client-ID 0SYo2Oy0ReRmqBiXPvedNHPu9aSxareRgPza6HApL5g',
    }
    MAX_ITEMS_ON_PAGE = 30

    def __init__(self):
        self.results = []
        self.x_count = '0'

    async def get_photos_by_proxy(self, limit: int, offset: int) -> tuple:
        redis = aioredis.from_url(
            "redis://172.19.0.3", encoding="utf-8"
        )
        key = f'{offset}:{limit}'

        if cache := await redis.hgetall(key):
            cache = {k.decode('utf-8'): v for k, v in cache.items()}
            self.x_count = str(int(cache['count_photos']))
            self.results.extend(pickle.loads(cache['photos']))
        else:
            if limit > self.MAX_ITEMS_ON_PAGE:
                await self.do_request(self.MAX_ITEMS_ON_PAGE, offset)
                mutable_limit, mutable_offset = limit, offset

                while mutable_limit > self.MAX_ITEMS_ON_PAGE:
                    mutable_limit -= self.MAX_ITEMS_ON_PAGE
                    mutable_offset += 1
                    await self.do_request(mutable_limit, mutable_offset)
            else:
                await self.do_request(limit, offset)

            await redis.hset(key, mapping={"photos": pickle.dumps(self.results), "count_photos": self.x_count})

        return self.results, self.x_count

    async def do_request(self, limit: int, offset: int) -> None:
        photos = await self.get_response_and_save_total_count(f'{self.URL_API_PHOTOS}?page={offset}'
                                                              f'&per_page={limit}&order_by=popular')
        self.results.extend([Photo(id=item['id'], description=item['description'], image=item['urls']['regular'])
                             for item in json.loads(photos)])

    async def get_response_and_save_total_count(self, url) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADEARS) as response:
                self.x_count = response.headers['X-Total']
                return await response.text()
