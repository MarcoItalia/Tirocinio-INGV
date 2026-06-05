# IMPORT
from timestamp_manager import read_timestamp, save_last_timestamp
from netcdf4_h5_manager import h5_file_write
from datetime import datetime, timezone
import numpy as np
import zmq
import array
import os
import sys
import config_manager

if len(sys.argv) != 2:
    print(
        "Wrong number of arguments, expected \"password\" as an argument")
    sys.exit()

# CONFIG
config = config_manager.yaml_read("config.yaml")
SAVE_PATH = config.data_dir.save_path
PORT = config.socket.port
IP_ADDRESS = config.socket.ip
PROTOCOL = config.socket.protocol
QUEUE_DIM = config.data_dir.queue_dim
socket_str = f"{PROTOCOL}://{IP_ADDRESS}:{PORT}"

# CREATE DIR, if exist ignore the error
try:
    os.mkdir(SAVE_PATH)
except FileExistsError:
    pass

# ZMQ INITIALIZATION
# ZMQ connection
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(socket_str)
# ZMQ REQ/REP
socket.send(read_timestamp())
message1 = socket.recv()
message2 = socket.recv()
print(f"Connection started with {IP_ADDRESS}")

# DATA INITIALIZATION
# Getting information
data1 = array.array('i', message1[0:4])
COUNT = data1[0]
data1 = array.array('d', message1[4:])
TimeStamp = data1[0]
print(f"Recived data {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)}")
if COUNT == 1:
    data2 = array.array('d', message2[0:48])
    dt = data2[3]
    data2 = array.array('i', message2[48:64])
    Size_Dist = data2[1]-data2[0]
    Size_Frequence = data2[3]-data2[2]
    message3 = socket.recv()
    data3 = array.array('f', message3)
else:
    print("   ")
    print("Script stopped --->>>  Raw data is not a valid dataset")
    sys.exit()
# Constructing data
StrainRate = np.reshape(data3, (Size_Frequence + 1, Size_Dist + 1))
# Writing data
filenames = next(os.walk(SAVE_PATH), (None, None, []))[2]
if len(filenames) < QUEUE_DIM:
    print("Writing in the Queue")
    h5_file_write(f"{SAVE_PATH}/{str(int(TimeStamp))}",
                  StrainRate, TimeStamp, dt)
else:
    print(
        f"Queue Full, lost {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)} data")

save_last_timestamp(TimeStamp)


i = 0
# CONTINOUS COLLECTION
while i < 10:  # True

    print()

    # ZMQ REQ/REP
    # reconnect ?
    socket.send(np.double(TimeStamp))
    message1 = socket.recv()
    message2 = socket.recv()
    message3 = socket.recv()

    # Getting information
    data2 = array.array('d', message2[0:48])
    dt = data2[3]
    data2 = array.array('i', message2[48:64])
    Size_Dist = data2[1]-data2[0]  # channels
    Size_Frequence = data2[3]-data2[2]  # frequences
    data1 = array.array('d', message1[4:])
    print(f"Recived data {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)}")

    if TimeStamp < data1[0]:
        i += 1
        TimeStamp = data1[0]
        data3 = array.array('f', message3)
        StrainRate = np.reshape(data3, (Size_Frequence + 1, Size_Dist+1))
        filenames = next(os.walk(SAVE_PATH), (None, None, []))[
            2]
        if len(filenames) < QUEUE_DIM:
            print("Writing in the Queue")
            h5_file_write(f"{SAVE_PATH}/{str(int(TimeStamp))}",
                          StrainRate, TimeStamp, dt)
        else:
            print(
                f"Queue Full, lost {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)} data")

        save_last_timestamp(TimeStamp)
