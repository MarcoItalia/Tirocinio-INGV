from netCDF4 import Dataset  # pylint: disable=no-name-in-module
import numpy as np
import os

FREQUENCES = 525
OVERLAP = 0
CHANNEL_START = 0
CHANNEL_END = 300 + 1


file_read = Dataset(
    "SR_DS_GL20_production_2026-03-01_12-00-29_UTC.h5", 'r')
# list((list((list(file_read.groups.keys())[0]).groups.keys())[0]).groups.keys())[0]
read_grp1 = list(file_read.groups.keys())[0]
read_grp2 = file_read.groups[read_grp1]
read_grp3 = read_grp2.groups[list(read_grp2.groups.keys())[0]]
read_grp4 = read_grp3.groups[list(read_grp3.groups.keys())[0]]
read_dataset = read_grp4.variables.get("Strain Rate [nStrain|s]")

for i in range(read_dataset.shape[0]):
    file_write = Dataset(f"{i}.0.h5", 'w')
    write_grp1 = file_write.createGroup("dataset")
    dataset_shape0 = write_grp1.createDimension("Time", None)
    dataset_shape1 = write_grp1.createDimension(
        "Frequences", FREQUENCES - OVERLAP)
    dataset_shape2 = write_grp1.createDimension(
        "Channels", CHANNEL_END - CHANNEL_START)
    write_dataset = write_grp1.createVariable("StrainRate", datatype="float32", dimensions=(
        dataset_shape0, dataset_shape1, dataset_shape2))
    write_dataset[0, :, :] = read_dataset[i,
                                          :, CHANNEL_START:CHANNEL_END]
    write_grp1.setncattr("Timestamp", read_grp4.getncattr("AcqStartTime"))
    write_grp1.setncattr("Channel_start", np.short(CHANNEL_START))
    write_grp1.setncattr("Channel_end", np.short(CHANNEL_END))
    write_grp1.setncattr("Location", "Niscemi")
    write_grp1.setncattr("dt_millisec", 5)

    file_write.close()


file_read.close()
