from netCDF4 import Dataset  # pylint: disable=no-name-in-module
import numpy as np
import os
import config_manager

# to move in config.yaml
CONFIG = config_manager.yaml_read("config.yaml")
OVERLAP = CONFIG.data_window.overlap  # config
CHANNEL_START = CONFIG.data_window.channel_start  # config
CHANNEL_END = CONFIG.data_window.channel_end  # config
LOCATION = CONFIG.data_window.location  # config


def h5_file_read(path_netcdf: str, callback):
    """Return the first read variable"""
    with Dataset(path_netcdf, 'r') as file_read:
        var = read_first_variable(file_read)
        if var is not None:
            return callback(var)


def read_first_variable(group):
    """Recursive read of .h5 group, until it finds a variable"""
    if group.variables:
        return next(iter(group.variables.values()))
    for grp in group.groups.values():
        result = read_first_variable(grp)
        if result is not None:
            return result
    return None


def process(var):
    """Callback function, doesn't do much outside"""
    return var[:, :, ]


def h5_file_write(path_netcdf: str, dataset, timestamp, dt):
    """Write h5 file from the path. The format is specific, Group-> Dataset | Attributes. Try to set the attributes if they are given, else None"""
    position = path_netcdf.find(".h5")
    if position != -1:
        path_netcdf = path_netcdf[:position]
    file_write = Dataset(path_netcdf, 'w')

    write_grp1 = file_write.createGroup("dataset")
    if dataset.ndim == 2:
        dataset_shape0 = write_grp1.createDimension("Time", 1)
        dataset_shape1 = write_grp1.createDimension(
            "Frequences", dataset.shape[0] - OVERLAP)
    else:
        dataset_shape0 = write_grp1.createDimension("Time", None)
        dataset_shape1 = write_grp1.createDimension(
            "Frequences", dataset.shape[1] - OVERLAP)

    dataset_shape2 = write_grp1.createDimension(
        "Channels", CHANNEL_END + 1 - CHANNEL_START)
    # list((list((list(file_read.groups.keys())[0]).groups.keys())[0]).groups.keys())[0]

    write_dataset = write_grp1.createVariable("StrainRate", datatype="float32", dimensions=(
        dataset_shape0, dataset_shape1, dataset_shape2))
    if dataset.ndim == 2:
        write_dataset[0, :, :] = dataset[:-OVERLAP,
                                         CHANNEL_START:CHANNEL_END+1]
    else:
        write_dataset[:, :, :] = dataset[:,
                                         :-OVERLAP, CHANNEL_START:CHANNEL_END+1]
    write_grp1.setncattr("Timestamp", timestamp)
    write_grp1.setncattr("Channel_start", np.short(CHANNEL_START))
    write_grp1.setncattr("Channel_end", np.short(CHANNEL_END))
    write_grp1.setncattr("Location", LOCATION)
    write_grp1.setncattr("dt_millisec", np.short(dt))

    file_write.close()

    os.replace(path_netcdf, f"{path_netcdf}.h5")
