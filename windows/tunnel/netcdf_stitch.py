"""
netcdf_stitch.py
-----------------
Watches a local directory for per-second HDF5 files produced by the
acquisition server, stitches up to 60 of them into a single output file
using H5Stitcher, then removes the originals.
"""

from os import path, listdir, remove, replace, mkdir
from time import sleep
from datetime import datetime, timezone
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from numpy import double

from netcdf4_h5_manager import H5Stitcher, read_attribute
from config_manager import yaml_read

config = yaml_read("config.yaml")

FILE_EXT = config.extension
PATH_DATA = config.paths.path_local + "/"
PATH_TO_SAVE = config.paths.complete_local_save_dir + "/"

FILES_PER_STITCH = config.data_window.seconds_to_aggregate
MAX_CONSECUTIVE_FAILS = 10

try:
    mkdir(PATH_TO_SAVE)
except FileExistsError:
    pass


def wait_for_first_file() -> str:
    """Block until at least one matching file appears; return its timestamp string."""
    while True:
        print("Checking for file in the directory")
        dir_list = sorted(listdir(PATH_DATA))
        for file in dir_list:
            pos_extension = file.find(FILE_EXT)
            if pos_extension != -1:
                return file[:pos_extension]
        sleep(0.5)


def stitch(timestamp_str: str) -> None:
    """Stitch up to FILES_PER_STITCH chunks starting at timestamp_str."""
    timestamp = double(timestamp_str)
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    tmp_path = f"{PATH_TO_SAVE}download_incomplete.tmp"
    prefix = "UNK"

    with Dataset(tmp_path, "w") as file_write:
        stitcher = H5Stitcher(file_write)

        fail_count = 0
        i = 0
        dt_to_aggregate = 0

        while i < FILES_PER_STITCH:
            file_path = path.join(PATH_DATA, f"{timestamp + i}{FILE_EXT}")

            try:
                with Dataset(file_path, "r") as file_read:
                    dt = read_attribute(file_read, "dt_millisec")
                    if i == 0:
                        dt_to_aggregate = dt
                        prefix = read_attribute(file_read, "Location")
                    elif dt != dt_to_aggregate:
                        break

                    stitcher.append(file_read, timestamp, dt)

                i += 1
                fail_count = 0

                try:
                    remove(file_path)
                except FileNotFoundError as e:
                    print(
                        f"File {timestamp + i - 1}{FILE_EXT} not found for removal.")
                    print(f"Exception: {e}\n")

            except FileNotFoundError:
                print(f"File {timestamp + i}{FILE_EXT} not found.")
                if fail_count < MAX_CONSECUTIVE_FAILS:
                    print("Waiting for file..")
                    fail_count += 1
                    sleep(0.5)
                else:
                    print("Searching for new start.\n")
                    break

    if len(prefix) > 3:
        prefix = str(prefix)[:3]
    prefix = prefix.upper()
    out_name = f"{PATH_TO_SAVE}{prefix}_{date.strftime('%Y%m%d-%H%M%S')}.h5"
    replace(tmp_path, out_name)
    print(f"Output written → {out_name}")


def main() -> None:
    while True:
        timestamp_str = wait_for_first_file()
        print(f"\nStitching {timestamp_str}\n")
        stitch(timestamp_str)


if __name__ == "__main__":
    main()
