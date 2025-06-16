from twc import compositor, map_utils, radar_frame, api 
import asyncio
import logging
from os import listdir, remove, mkdir
from os.path import exists
from shutil import rmtree
from argparse import ArgumentParser

logger = logging.getLogger(__name__)

# CLI arguments
arg_parser = ArgumentParser(prog='i2radar')
arg_parser.add_argument("-f", "--fresh", action="store_true", default=False,
                        help="Delete previously stored radar frames")

arg_parser.add_argument("-t", "--radar-type", dest="radar_type", default="Radar-US",
                        help="Sets the image sequence definition.")

args = arg_parser.parse_args()

async def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers= [logging.FileHandler('i2radar.log'), logging.StreamHandler()])
    logger.info('Starting i2Radar..')

    # Re-create the tile output directory to avoid unfinished frames not being generated
    if not exists("./output/tiles"):
        mkdir("./output/tiles")
    else:
        rmtree("./output/tiles")
        mkdir("./output/tiles")

    if not exists("./output/frames"):
        mkdir("./output/frames")

    if args.fresh:
        rmtree("./output/frames")
        mkdir("./output/frames")


    await compositor.make_radar_frames(args.radar_type)

    # Enter radar loop
    while True:
        await asyncio.sleep(300)
        await compositor.make_radar_frames(args.radar_type)


async def clear_old_frames(current_timestamps: list[int]):
    files_deleted = 0

    for i in listdir("./output/frames"):
        file_timestamp = int(i.split(".tiff")[0])

        if file_timestamp in current_timestamps:
            continue

        remove("./output/frames/" + i)
        files_deleted += 1

    logger.info(f"Cleared {files_deleted} radar frames.")


if __name__ == "__main__":
    asyncio.run(main())