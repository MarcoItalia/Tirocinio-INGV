from netCDF4 import Dataset  # pylint: disable=no-name-in-module
import numpy as np
import os

FREQUENCES = 520
CHANNEL_START = 150
CHANNEL_END = 300


def read_variable(group, var_search: str) -> Dataset:
    """Recursive read of .h5 group, until it finds a variable"""
    try:
        return group.variables[var_search]
    except KeyError:
        for grp in group.groups.values():
            result = read_variable(grp, var_search)
            if result is not None:
                return result
        return None


file_read = Dataset(
    "SR_DS_GL20_production_2026-03-01_12-00-29_UTC.h5", 'r')
file_write = Dataset("try3", 'w')

write_grp1 = file_write.createGroup("dataset")
dataset_shape0 = write_grp1.createDimension("Time", None)
dataset_shape1 = write_grp1.createDimension("Frequences", FREQUENCES)
dataset_shape2 = write_grp1.createDimension(
    "Channels", CHANNEL_END + 1 - CHANNEL_START)
# list((list((list(file_read.groups.keys())[0]).groups.keys())[0]).groups.keys())[0]
read_grp1 = list(file_read.groups.keys())[0]
read_grp2 = file_read.groups[read_grp1]
read_grp3 = read_grp2.groups[list(read_grp2.groups.keys())[0]]
read_grp4 = read_grp3.groups[list(read_grp3.groups.keys())[0]]
read_dataset = read_grp4.variables.get("Strain Rate [nStrain|s]")

write_dataset = write_grp1.createVariable("StrainRate", datatype="float32", dimensions=(
    dataset_shape0, dataset_shape1, dataset_shape2))
write_dataset[:, :, :] = read_dataset[:,
                                      :FREQUENCES, CHANNEL_START:CHANNEL_END+1]
write_grp1.setncattr("Timestamp", read_grp4.getncattr("AcqStartTime"))
write_grp1.setncattr("Channel_start", np.short(CHANNEL_START))
write_grp1.setncattr("Channel_end", np.short(CHANNEL_END))
write_grp1.setncattr("Location", "Niscemi")
write_grp1.setncattr("dt", np.short(write_dataset.shape[0]))


file_read.close()
file_write.close()

os.replace("try3", "try3.h5")

with Dataset("try3.h5", 'r') as file_read:
    print(read_variable(file_read, "StrainRate"))
