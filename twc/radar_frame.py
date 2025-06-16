from datetime import datetime
import math

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class LatLong():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ImageBoundaries():
    def __init__(
            self,
            lower_left_long,
            lower_left_lat,
            upper_right_long,
            upper_right_lat,
            vertical_adjustment,
            original_img_height,
            original_img_width,
            images_interval,
            expiration
    ):
        
        self.lower_left_long = lower_left_long
        self.lower_left_lat = lower_left_lat
        self.upper_right_long = upper_right_long 
        self.upper_right_lat = upper_right_lat

        self.vertical_adjustment = vertical_adjustment

        self.original_img_height = original_img_height
        self.original_img_width = original_img_width
        self.images_interval = images_interval
        self.expiration = expiration


    def get_upper_right(self) -> LatLong:
        return LatLong(
            x = self.upper_right_lat,
            y = self.upper_right_long
        )
        
    def get_upper_left(self) -> LatLong:
        return LatLong(
            x = self.upper_right_lat,
            y = self.lower_left_long
        )
        
    def get_lower_right(self) -> LatLong:
        return LatLong(
            x = self.lower_left_lat,
            y = self.upper_right_long
        )
        
    def get_lower_left(self) -> LatLong:
        return LatLong(
            x = self.lower_left_lat,
            y = self.lower_left_long
        )