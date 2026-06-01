import h5py
import numpy as np
import os

CHANNEL_START = 150
CHANNEL_END = 300

os.system('cls' if os.name == 'nt' else 'clear')

file_read = h5py.File("SR_DS_GL20_production_2026-03-01_12-00-29_UTC.h5", 'r')
file_out = h5py.File("try2", 'w')
# print(type(list(file_read.keys())[0]))

# file_read.copy((list(file_read.keys())[0]), file_out)
grp1 = file_out.create_group("dataset")
# print((list((list((list(file_read.values())[0]).values())[0]).values())[0]).attrs.get("AcqStartTime"))
grp1.attrs.create("timestamp", (list((list((list(file_read.values())[0]).values())[0]).values())[
    0]).attrs.get("AcqStartTime"))
grp1.attrs.create("channel_start", CHANNEL_START, dtype=np.short)
grp1.attrs.create("channel_end", CHANNEL_END, dtype=np.short)
grp1.attrs.create("dt", list((list((list((list(file_read.values())[0]).values())[0]).values())[
    0]).values())[0].shape[0], dtype=np.short)


dataset = list(
    (list((list((list(file_read.values())[0]).values())[0]).values())[0]).values())[0]
dataset = dataset[:, :520, CHANNEL_START:CHANNEL_END+1]
print(dataset.shape)
data1 = grp1.create_dataset("Dataset_Strain_rate", data=dataset)

data1.dims[0].label = 'Time'
data1.dims[1].label = 'Frequences'
data1.dims[2].label = 'Channels'


file_read.close()
file_out.close()
