from PIL import Image as PILImage
from wand.image import Image as wandImage
from wand.color import Color
from multiprocessing import Pool
from twc import map_utils, api
from twc.radar_frame import ImageBoundaries, Point
from os import listdir, cpu_count
from shutil import rmtree
from os.path import exists
import logging
from main import clear_old_frames

logger = logging.getLogger(__name__)

temp_api_key = "71f92ea9dd2f4790b92ea9dd2f779061"

def palette_convert(image_path: str):

    img = wandImage(filename = image_path)

    
    rainColors = [
        Color('rgb(64,204,85'), # lightest green
        Color('rgb(0,153,0'), # med green
        Color('rgb(0,102,0)'), # darkest green
        Color('rgb(191,204,85)'), # yellow
        Color('rgb(191,153,0)'), # orange
        Color('rgb(255,51,0)'), # ...
        Color('rgb(191,51,0)'), # red
        Color('rgb(64,0,0)') # dark red
    ]

    mixColors = [
        Color('rgb(253,130,215)'), # light purple
        Color('rgb(208,94,176)'), # ...
        Color('rgb(190,70,150)'), # ...
        Color('rgb(170,50,130)') # dark purple
    ]

    snowColors = [
        Color('rgb(150,150,150)'), # dark grey
        Color('rgb(180,180,180)'), # light grey
        Color('rgb(210,210,210)'), # grey
        Color('rgb(230,230,230)') # white
    ]

    # Replace rain colors
    img.opaque_paint(Color('rgb(99, 235, 99)'), rainColors[0], 7000.0)
    img.opaque_paint(Color('rgb(28,158,52)'), rainColors[1], 7000.0)
    img.opaque_paint(Color('rgb(0, 63, 0)'), rainColors[2], 7000.0)

    img.opaque_paint(Color('rgb(251,235,2)'), rainColors[3], 7000.0)
    img.opaque_paint(Color('rgb(238, 109, 2)'), rainColors[4], 7000.0)
    img.opaque_paint(Color('rgb(210,11,6)'), rainColors[5], 7000.0)
    img.opaque_paint(Color('rgb(169,5,3)'), rainColors[6], 7000.0)
    img.opaque_paint(Color('rgb(128,0,0)'), rainColors[7], 7000.0)

    # Replace mix colors
    img.opaque_paint(Color('rgb(255,160,207)'), mixColors[0], 7000.0)
    img.opaque_paint(Color('rgb(217,110,163)'), mixColors[1], 7000.0)
    img.opaque_paint(Color('rgb(192,77,134)'), mixColors[2], 7000.0)
    img.opaque_paint(Color('rgb(174,51,112)'), mixColors[3], 7000.0)
    img.opaque_paint(Color('rgb(146,13,79)'), mixColors[3], 7000.0)

    # Replace snow colors
    img.opaque_paint(Color('rgb(138,248,255)'), snowColors[0], 7000.0)
    img.opaque_paint(Color('rgb(110,203,212)'), snowColors[1], 7000.0)
    img.opaque_paint(Color('rgb(82,159,170)'), snowColors[2], 7000.0)
    img.opaque_paint(Color('rgb(40,93,106)'), snowColors[3], 7000.0)
    img.opaque_paint(Color('rgb(13,49,64)'), snowColors[3]), 7000.0

    img.compression = 'lzw'
    img.save(filename=image_path)




async def make_radar_frames(radar_type: str):
    logger.info("Creating radar frames..")


    combined_coordinates = []

    boundaries = map_utils.boundaries_from_json(radar_type)
    upper_right = boundaries.get_upper_right()
    lower_left = boundaries.get_lower_left()
    upper_left = boundaries.get_upper_left()
    lower_right = boundaries.get_lower_right()

    tile_img_bounds = map_utils.calculate_bounds(upper_right, lower_left, upper_left, lower_right)
    valid_times = await api.get_valid_timestamps(boundaries)

    await clear_old_frames(valid_times)

    # Get list of invalid radar frames
    for i in listdir("./output/tiles/"):
        if i.split('.')[0] not in [str(x) for x in valid_times] and i != "Thumbs.db":
            rmtree("./output/tiles/" + i) 

    # Calculate frame tile coordinates
    for y in range(tile_img_bounds.y_start, tile_img_bounds.y_end):
        if y <= tile_img_bounds.y_end:
            for x in range(tile_img_bounds.x_start, tile_img_bounds.x_end):
                if x <= tile_img_bounds.x_end:
                    combined_coordinates.append(Point(x, y))


    urls = []
    paths = []
    filenames = []

    for i in range(0, len(valid_times)):
        for c in range(0, len(combined_coordinates)):
            if not exists(f"./output/frames/{valid_times[i]}.tiff"):
                urls.append(f"https://api.weather.com/v3/TileServer/tile?product=twcRadarMosaic&ts={str(valid_times[i])}" +
                            f"&xyz={combined_coordinates[c].x}:{combined_coordinates[c].y}:6" +
                            f"&apiKey={temp_api_key}")  # TODO: Set this to use an environment variable
                paths.append(f"./output/tiles/{valid_times[i]}")
                filenames.append(f"{valid_times[i]}_{combined_coordinates[c].x}_{combined_coordinates[c].y}.png")


    if len(urls) != 0 and len(urls) >= 6:
        with Pool(cpu_count() -1) as p:
            p.starmap(api.download_radar_tile, zip(urls, paths, filenames))
            p.close()
            p.join()
    elif len(urls) < 6 and len(urls) != 0:
        with Pool(len(urls)) as p:
            p.starmap(api.download_radar_tile, zip(urls, paths, filenames))
            p.close()
            p.join()
    elif len(urls) == 0:
        return
    

    imgs_to_generate = []
    frames_to_composite = []
    finished = []
    files = []

    for t in valid_times:
        imgs_to_generate.append(PILImage.new("RGB", (tile_img_bounds.image_width, tile_img_bounds.image_height)))

    
    # Stitch the radar tiles
    for i in range(0, len(imgs_to_generate)):
        logger.info(f"Stitching radar tile {i + 1}/{len(imgs_to_generate)}..")
        if not exists(f"./output/frames/{valid_times[i]}.tiff"):
            for c in combined_coordinates:
                path = f"./output/tiles/{valid_times[i]}/{valid_times[i]}_{c.x}_{c.y}.png"

                x_placement = (c.x - tile_img_bounds.x_start) * 256
                y_placement = (c.y - tile_img_bounds.y_start) * 256

                place_tile = PILImage.open(path)

                imgs_to_generate[i].paste(place_tile, (x_placement, y_placement))

            # Don't render with the alpha channel.
            imgs_to_generate[i].save(f"./output/frames/{valid_times[i]}.tiff", compression = 'tiff_lzw')
            frames_to_composite.append(f"./output/frames/{valid_times[i]}.tiff")

            rmtree(f"./output/tiles/{valid_times[i]}")


    # Composite the images with the WxPro palette
    images_processed = 0
    for image in frames_to_composite:
        images_processed += 1
        logger.info(f"Compositing frame {images_processed}/{len(frames_to_composite)}")
        image_raw = wandImage(filename=image)
        image_raw.crop(tile_img_bounds.upper_left_x,
                        tile_img_bounds.upper_left_y,
                        width = int(tile_img_bounds.lower_right_x - tile_img_bounds.upper_left_x),
                        height = int(tile_img_bounds.lower_right_y - tile_img_bounds.upper_left_y))
        image_raw.compression = 'lzw'

        image_raw.save(filename = image)

        # Resize the frame into the radar type's desired dimensions
        image_pil = PILImage.open(image)
        image_pil = image_pil.resize((boundaries.original_img_width, boundaries.original_img_height), 0)
        image_pil.save(image)
        palette_convert(image)

        finished.append(image)

    logger.info(f"Created {len(finished)} new radar frames.")
