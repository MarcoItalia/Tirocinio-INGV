from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from datetime import datetime
import time
import os
import sys
import netcdf4_h5_manager
import config_manager

config = config_manager.yaml_read("config.yaml")

FILE_EXT = config.extension
PATH_DATA = config.paths.local_save_dir + "/"

# start cycle
# while True:

check_first = False
while not check_first:
    dir_list = os.listdir(PATH_DATA)  # pylint: disable=redefined-builtin
    dir_list.sort()
    if dir_list != []:
        for file in dir_list:
            pos_extension = file.find(FILE_EXT)
            if FILE_EXT != -1:
                timestamp = file[:pos_extension]
                check_first = True
                break
    else:
        time.sleep(0.5)
print(time.time())
# sys.exit()


for i in range(60):  # sto sbagliando tutto
    # can add try except to intercept error when there are missing seconds
    try:
        file_read = Dataset(f"{timestamp+i}{FILE_EXT}", 'r')
        dataset_to_copy = netcdf4_h5_manager.read_first_variable(file_read)
        netcdf4_h5_manager.h5_file_write(
            # dovrei leggerlo dinamicamente il dt, meglio mettere una funzione nel modulo netcdf4_h5_manager
            f"{timestamp+i}", dataset_to_copy, timestamp, 5)
        try:
            os.remove(f"{timestamp+i}{FILE_EXT}")
        except FileNotFoundError:
            print(f"File {timestamp+i}{FILE_EXT} not found.")
    except FileNotFoundError:
        break
date = datetime.fromtimestamp(timestamp)
os.replace(
    f"{timestamp+1}{FILE_EXT}", f"CL_{date.strftime('%Y%m%d-%H%M%S')}.h5")

# end cycle
