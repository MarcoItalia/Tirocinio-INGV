from os import path, listdir, remove, replace, mkdir
from time import sleep
from datetime import datetime, timezone
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from numpy import double
from netcdf4_h5_manager import H5Stitcher, read_attribute
from yaml_manager import yaml_read
import numpy as np

config = yaml_read("config.yaml")

FILE_EXT = config["extension"]
PATH_DATA = config["paths"]["path_local"] + "/"
PATH_TO_SAVE = config["paths"]["complete_local_save_dir"] + "/"
INFO_PATH = config["paths"]["info_dir"] + "/" + "_add_info.yaml"

FILES_PER_STITCH = config["data_window"]["seconds_to_aggregate"]
MAX_CONSECUTIVE_FAILS = 10


def dicts_are_equal(dict1: dict, dict2: dict) -> bool:
    """
    Check if the dictionary are equals. Return a bool.
    Python have a built in check for dictionary confronts,
    dict == dict2 works, but that confront value per value, and ends up
    confronting arrays in this case. Confronting arrays raise a ValueError.
    Parameters
    ----------
    dict1: dict
    dict2: dict
    """

    if dict1.keys() != dict2.keys():
        return False
    for key in dict1:
        v1, v2 = dict1[key], dict2[key]
        if isinstance(v1, np.ndarray) or isinstance(v2, np.ndarray):
            if not np.array_equal(v1, v2):
                return False
        elif v1 != v2:
            return False
    return True


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


def stitch(timestamp_str: str, add_info_bool) -> None:
    """Stitch up to FILES_PER_STITCH chunks starting at timestamp_str."""
    timestamp = double(timestamp_str)
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    tmp_path = f"{PATH_TO_SAVE}download_incomplete.tmp"
    prefix = "UNK"

    with Dataset(tmp_path, "w") as file_write:
        stitcher = H5Stitcher(file_write, add_info_bool)

        fail_count = 0
        i = 0
        dt_to_aggregate = 0
        add_info = {}

        while i < FILES_PER_STITCH:
            file_path = path.join(
                PATH_DATA, f"{timestamp + i}{FILE_EXT}")
            # print(f"Now {file_path}\n")
            try:
                with Dataset(file_path, "r") as file_read:
                    dt = read_attribute(file_read, "dt_millisec")
                    if i == 0:
                        # read info and put it in saved_dict
                        try:
                            if add_info_bool:
                                add_info = yaml_read(INFO_PATH)
                        except FileNotFoundError:
                            add_info_bool = False
                            print("Info file not found, check the dir")
                            print(
                                "Stitching will resume without the additional info.\n\n")
                        dt_to_aggregate = dt
                        prefix = read_attribute(file_read, "Location")
                    elif dt != dt_to_aggregate:
                        print("Break, dt changed")
                        break
                    # check if the info changed from the last time
                    elif add_info_bool and not dicts_are_equal(add_info, yaml_read(INFO_PATH)):
                        print("Break, something changed in the specifics!")
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
    print(f"Output written: {out_name}")


def main() -> None:
    """
    netcdf_stitch.py
    -----------------
    Watches a local directory for per-second HDF5 files produced by the
    acquisition server, stitches up to FILES_PER_STITCH of them into a single output file
    using H5Stitcher, then removes the originals.
    """

    try:
        mkdir(PATH_TO_SAVE)
    except FileExistsError:
        pass

    while True:
        timestamp_str = wait_for_first_file()
        print(f"\nStitching {timestamp_str}\n")
        stitch(timestamp_str, add_info_bool=True)


if __name__ == "__main__":
    main()
