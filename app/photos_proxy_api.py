import json
import aiohttp
import aioredis

from app.models import Photo


class PhotosProxyApi:
    URL_API_PHOTOS = 'https://api.unsplash.com/photos'
    HEADEARS = {
        'Authorization': 'Client-ID 0SYo2Oy0ReRmqBiXPvedNHPu9aSxareRgPza6HApL5g',
    }

    async def get_custom_photos(self, limit: int, offset: int) -> tuple:
        # use ip redis docker container
        redis = aioredis.from_url(
            "redis://172.19.0.3", encoding="utf-8", decode_responses=True
        )
        key = f'{offset}:{limit}'

        photos = await redis.get(f'{key}-photos')
        count_photos = await redis.get(f'{key}-count_photos')

        if photos and count_photos:
            return await self.prepare_result(photos, count_photos)
        else:
            url = f'{self.URL_API_PHOTOS}?page={offset}&per_page={limit}&order_by=popular'
            photos, count_photos = await self.aio_request(url)
            await redis.set(f'{key}-photos', photos, ex=1800)
            await redis.set(f'{key}-count_photos', count_photos, ex=1800)

        return await self.prepare_result(photos, count_photos)

    @staticmethod
    async def prepare_result(photos: str, count_photos: str) -> tuple:
        json_ = json.loads(photos)

        return [Photo(id=item['id'], description=item['description'], image=item['urls']['regular'])
                for item in json_], count_photos

    async def aio_request(self, url) -> tuple:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.HEADEARS) as response:
                return await response.text(), response.headers['X-Total']
