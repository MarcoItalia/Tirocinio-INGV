from os import path, listdir, remove, replace, mkdir
from time import sleep
from datetime import datetime
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from numpy import double
import netcdf4_h5_manager
from config_manager import yaml_read

config = yaml_read("config.yaml")

FILE_EXT = config.extension
PATH_DATA = config.paths.path_local + "/"
PATH_TO_SAVE = PATH_DATA + config.paths.complete_local_save_dir + "/"

# mkdir if it doesn't exist
try:
    mkdir(PATH_TO_SAVE)
except FileExistsError:
    pass


while True:

    first_found = False
    while not first_found:
        print("Checking for file in the directory")
        dir_list = listdir(PATH_DATA)  # pylint: disable=redefined-builtin
        dir_list.sort()
        if dir_list != []:
            for file in dir_list:
                pos_extension = file.find(FILE_EXT)
                if pos_extension != -1:
                    timestamp = file[:pos_extension]
                    first_found = True
                    break
        sleep(0.5)

    print(f"\nStitching {timestamp}\n")

    date = datetime.fromtimestamp(double(timestamp))
    with Dataset(f"{PATH_TO_SAVE}CL_{date.strftime('%Y%m%d-%H%M%S')}", 'w') as file_write:

        fail_count = 0
        i = 0

        while i < 60:
            try:
                file_path = path.join(
                    PATH_DATA, f"{double(timestamp)+i}{FILE_EXT}")
                with Dataset(file_path, 'r') as file_read:
                    dataset_to_copy = netcdf4_h5_manager.read_first_variable(
                        file_read)
                    netcdf4_h5_manager.h5_file_write(
                        file_write, dataset_to_copy, timestamp, netcdf4_h5_manager.read_attribute(file_read, "dt"), position=i)
                    i += 1
                    fail_count = 0

                try:
                    remove(file_path)
                except FileNotFoundError as e:
                    print(f"File {double(timestamp)+i-1}{FILE_EXT} not found.")
                    print(f"Exception: {e}\n")

            except FileNotFoundError as e:
                print(f"File {double(timestamp)+i}{FILE_EXT} not found")
                print(f"Exception: {e}\n")
                if fail_count < 10:
                    fail_count += 1
                    sleep(0.5)
                else:
                    break

    replace(f"{PATH_TO_SAVE}CL_{date.strftime('%Y%m%d-%H%M%S')}",
            f"{PATH_TO_SAVE}CL_{date.strftime('%Y%m%d-%H%M%S')}.h5")
