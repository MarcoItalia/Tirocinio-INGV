from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from os import replace
import numpy as np
import config_manager

CONFIG = config_manager.yaml_read("config.yaml")
OVERLAP = CONFIG.data_window.overlap  # config
CHANNEL_START = CONFIG.data_window.channels_start  # config
CHANNEL_END = CONFIG.data_window.channels_end  # config
LOCATION = CONFIG.data_window.location  # config


def h5_file_read(path_netcdf: str, callback):
    """Return the first read variable"""
    with Dataset(path_netcdf, 'r') as file_read:
        var = read_first_variable(file_read)
        if var is not None:
            return callback(var)


def read_first_variable(group) -> Dataset:
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


def read_attribute(path_netcdf, attr: str = "dt"):
    """Read attribute passed in the function"""

    if isinstance(path_netcdf, str):
        with Dataset(path_netcdf, 'r') as file_read:
            for group in file_read.groups.values():
                try:
                    attr_value = group.getncattr(attr)
                    return attr_value
                except AttributeError:
                    pass
            return None
    elif isinstance(path_netcdf, Dataset):
        for group in path_netcdf.groups.values():
            try:
                attr_value = group.getncattr(attr)
                return attr_value
            except AttributeError:
                pass
        return None
    return None


def _initialize(dataset_instance, dataset, timestamp, dt):
    write_grp1 = dataset_instance.createGroup("dataset")
    write_grp1.setncattr("Timestamp", timestamp)
    write_grp1.setncattr("Channel_start", np.short(CHANNEL_START))
    write_grp1.setncattr("Channel_end", np.short(CHANNEL_END))
    write_grp1.setncattr("Location", LOCATION)
    write_grp1.setncattr("dt_millisec", np.short(dt))
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

    write_grp1.createVariable("StrainRate", datatype="float32", dimensions=(
        dataset_shape0, dataset_shape1, dataset_shape2))


def _asign(dataset_write, dataset_read, position):
    if OVERLAP > 0:
        if dataset_read.ndim == 2:
            dataset_write[position, :, :] = dataset_read[:-OVERLAP,
                                                         CHANNEL_START:CHANNEL_END+1]
        else:
            dataset_write[position:, :, :] = dataset_read[:,
                                                          :-OVERLAP, CHANNEL_START:CHANNEL_END+1]
    else:
        if dataset_read.ndim == 2:
            dataset_write[position, :, :] = dataset_read[:,
                                                         CHANNEL_START:CHANNEL_END+1]
        else:
            dataset_write[position:, :, :] = dataset_read[:,
                                                          :, CHANNEL_START:CHANNEL_END+1]
    return dataset_write


def h5_file_write(path_netcdf, dataset, timestamp, dt, position: int = 0):
    """Write h5 file from the path or Dataset. The format is specific, Group-> Dataset | Attributes"""
    if isinstance(path_netcdf, str):
        pos_ext = path_netcdf.find(".h5")
        if pos_ext != -1:
            path_netcdf = path_netcdf[:pos_ext]
        file_write = Dataset(path_netcdf, 'w')
    elif isinstance(path_netcdf, Dataset):
        file_write = path_netcdf
    else:
        raise ValueError

    if "dataset" not in file_write.groups:
        _initialize(file_write, dataset, timestamp, dt)
        write_grp1 = file_write.groups["dataset"]
    else:
        write_grp1 = file_write.groups["dataset"]
        write_grp1.setncattr("dt_millisec", np.short(
            write_grp1.getncattr("dt_millisec")) + np.short(dt))

    write_dataset = write_grp1.variables["StrainRate"]

    write_dataset = _asign(write_dataset, dataset, position)

    if isinstance(path_netcdf, str):
        file_write.close()
        replace(path_netcdf, f"{path_netcdf}.h5")
