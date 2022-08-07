from fastapi import FastAPI, Response

from app.photos_proxy_api import PhotosProxyApi

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/photos")
async def get_photos(response: Response, limit: int = 10, offset: int = 1):
    photos, headers_count = await PhotosProxyApi().get_custom_photos(limit, offset)
    response.headers["X-Total"] = headers_count
    return photos
