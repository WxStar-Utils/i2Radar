import asyncio
import aiohttp
import requests
from twc.radar_frame import ImageBoundaries, LatLong
from datetime import datetime, timezone
from os import mkdir
from os.path import exists

class TileImageBounds():
    def __init__(self, upper_left_x, upper_left_y, lower_right_x, lower_right_y,
                 x_start, x_end, y_start, y_end, x_tiles, y_tiles, image_width,
                 image_height):
        self.upper_left_x = upper_left_x
        self.upper_left_y = upper_left_y
        self.lower_right_x = lower_right_x
        self.lower_right_y = lower_right_y
        self.x_start = x_start
        self.x_end = x_end
        self.y_start = y_start
        self.y_end = y_end
        self.x_tiles = x_tiles
        self.y_tiles = y_tiles
        self.image_width = image_width
        self.image_height = image_height


async def get_valid_timestamps(boundaries: ImageBoundaries) -> list:
    times = []
    temp_api_key = "71f92ea9dd2f4790b92ea9dd2f779061"

    async with aiohttp.ClientSession() as session:
        uri = f"https://api.weather.com/v3/TileServer/series/productSet?apiKey={temp_api_key}&filter=twcRadarMosaic"

        async with session.get(uri) as r:
            response = await r.json()

            for t in range(0, len(response['seriesInfo']['twcRadarMosaic']['series'])):

                if (t <= 35):
                    time = response['seriesInfo']['twcRadarMosaic']['series'][t]['ts']

                    if (time % boundaries.images_interval != 0):
                        continue
                    
                    if time < (datetime.now(timezone.utc).timestamp() / 1000 - boundaries.expiration):
                        continue

                    times.append(time)

    return times


def download_radar_tile(url, path, filename):
    image = requests.get(url, stream = True)
    timestamp = filename.split('_')[0]

    download = True

    if exists(f"./output/frames/{timestamp}.tiff"):
        download = False

    if exists(f"{path}/{filename}"):
        download = False

    if not exists(path):
        mkdir(path)

    if image.status_code == 200 and download:
        with open(f'{path}/{filename}', 'wb') as tile:
            for data in image:
                tile.write(data)
