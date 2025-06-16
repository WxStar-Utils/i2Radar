import math 
import json

from twc import radar_frame
from twc.api import TileImageBounds

def world_coordinate_to_tile(coordinates: radar_frame.Point) -> radar_frame.Point:
    scale = 1 << 6

    return radar_frame.Point(
        x = math.floor(coordinates.x * scale / 255),
        y = math.floor(coordinates.y * scale / 255)
    )


def world_coordinate_to_pixel(coordinates: radar_frame.Point) -> radar_frame.Point:
    scale = 1 << 6

    return radar_frame.Point(
        x = math.floor(coordinates.x * scale),
        y = math.floor(coordinates.y * scale)
    )

def lat_long_project(latitude, longitude) -> radar_frame.Point:
    sin_y = math.sin(latitude * math.pi / 180)
    sin_y = min(max(sin_y, -0.9999), 0.9999)

    return radar_frame.Point(
        x = 256 * (0.5 + longitude / 360),
        y = 256 * (0.5 - math.log(1 + sin_y) / (1 - sin_y) / (4 * math.pi))
    )

def calculate_bounds(upper_right: radar_frame.LatLong, lower_left: radar_frame.LatLong,
                     upper_left: radar_frame.LatLong, lower_right: radar_frame.LatLong) -> TileImageBounds:
    
    upper_right_tile: radar_frame.Point = world_coordinate_to_tile(lat_long_project(upper_right.x, upper_right.y))
    lower_left_tile: radar_frame.Point = world_coordinate_to_tile(lat_long_project(lower_left.x, lower_left.y))
    upper_left_tile: radar_frame.Point = world_coordinate_to_tile(lat_long_project(upper_left.x, upper_left.y))
    lower_right_tile: radar_frame.Point = world_coordinate_to_tile(lat_long_project(lower_right.x, lower_right.y))

    upper_left_pixels: radar_frame.Point = world_coordinate_to_pixel(lat_long_project(upper_left.x, upper_left.y))
    lower_right_pixels: radar_frame.Point = world_coordinate_to_pixel(lat_long_project(lower_right.x, lower_right.y))


    upper_left_x = upper_left_pixels.x - upper_left_tile.x * 256
    upper_left_y = upper_left_pixels.y - upper_left_tile.y * 256
    lower_right_x = lower_right_pixels.x - upper_left_tile.x * 256
    lower_right_y = lower_right_pixels.y - upper_left_tile.y * 256

    # x_start, y_start, etc. ensure that the downloaded tiles stay within the coordinates for the radar sequence
    x_start = int(upper_left_tile.x)
    x_end = int(upper_right_tile.x)
    y_start = int(upper_left_tile.y)
    y_end = int(lower_left_tile.y)



    x_tiles = x_end - x_start
    y_tiles = y_end - y_start

    image_width = 256 * (x_tiles + 1)
    image_height = 256 * (y_tiles + 1)

    bounds = TileImageBounds(
        upper_left_x,
        upper_left_y,
        lower_right_x,
        lower_right_y,
        x_start,
        x_end,
        y_start,
        y_end,
        x_tiles,
        y_tiles,
        image_width,
        image_height
    )

    return bounds

def boundaries_from_json(radar_type: str) -> radar_frame.ImageBoundaries:
    with open('ImageSequenceDefs.json', "r") as file:
        defs = json.loads(file.read())

    sequence = defs['ImageSequenceDefs'][radar_type]

    return radar_frame.ImageBoundaries(
        lower_left_lat = sequence['LowerLeftLat'],
        lower_left_long = sequence['LowerLeftLong'],
        upper_right_lat = sequence['UpperRightLat'],
        upper_right_long = sequence['UpperRightLong'],
        vertical_adjustment = sequence['VerticalAdjustment'],
        original_img_height = sequence['OriginalImageHeight'],
        original_img_width = sequence['OriginalImageWidth'],
        images_interval = sequence['ImagesInterval'],
        expiration = sequence['Expiration']
    )