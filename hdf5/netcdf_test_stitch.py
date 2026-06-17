from netCDF4 import Dataset  # pylint: disable=no-name-in-module
import numpy as np
from datetime import datetime, timezone
import os

FREQUENCES = 520
CHANNEL_START = 150
CHANNEL_END = 300


file_write = Dataset(
    "try4", 'w')
write_grp1 = file_write.createGroup("dataset")
dataset_shape0 = write_grp1.createDimension("Time", None)
dataset_shape1 = write_grp1.createDimension("Frequences", FREQUENCES)
dataset_shape2 = write_grp1.createDimension(
    "Channels", CHANNEL_END + 1 - CHANNEL_START)
write_dataset = write_grp1.createVariable("StrainRate", datatype="float32", dimensions=(
    dataset_shape0, dataset_shape1, dataset_shape2))


date = datetime.now()
# should define a module to find the next step in the real case
print(date)
for i in range(60):
    # can add try except to intercept error when there are missing seconds
    try:
        file_read = Dataset(f"n{i}.h5", 'r')
        read_grp1 = file_read.groups[list(file_read.groups.keys())[0]]
        if i == 0:
            timestamp = read_grp1.getncattr("Timestamp")
            write_grp1.setncattr("Timestamp", timestamp)
            date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            write_grp1.setncattr("Channel_start", np.short(CHANNEL_START))
            write_grp1.setncattr("Channel_end", np.short(CHANNEL_END))
            write_grp1.setncattr("Location", "Niscemi")
            write_grp1.setncattr("dt", np.short(write_dataset.shape[0]))

    # print(read_grp1)
        read_dataset = read_grp1.variables.get("Strain Rate Dataset")
        write_dataset[i, :, :] = read_dataset[0, :, :]
        file_read.close()
        # time.sleep(0.2)
        try:
            os.remove(f"n{i}.h5")
        except FileNotFoundError:
            print(f"File n{i}.h5 not found.")
    except FileNotFoundError:
        break


file_write.close()
os.replace(
    "try4", f"CL_{date.strftime('%Y%m%d-%H%M%S')}.h5")
