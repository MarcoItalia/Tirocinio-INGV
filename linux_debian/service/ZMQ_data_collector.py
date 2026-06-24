from os import mkdir, walk
from sys import exit as sys_exit
from threading import Thread
from datetime import datetime, timezone
from array import array
from numpy import reshape, double
from netcdf4_h5_manager import h5_file_write
from timestamp_manager import read_timestamp, save_last_timestamp
import ssh_file_reader
import zmq
import config_manager


# ── Config reader ──────────────────────────────
config = config_manager.yaml_read("config.yaml")

SAVE_PATH = config["paths"]["save_path"]
PORT = config["socket_zmq"]["port"]
IP_ADDRESS = config["socket_zmq"]["ip"]
PROTOCOL = config["socket_zmq"]["protocol"]
QUEUE_DIM = config["paths"]["queue_dim"]
SOCKET_STR = f"{PROTOCOL}://{IP_ADDRESS}:{PORT}"

# ── mkdir to store the downloaded files ──────────────────────────────
try:
    mkdir(SAVE_PATH)
except FileExistsError:
    pass

# ── Start a thread to download complete file and read add info ──────────────────────────────

t = Thread(target=ssh_file_reader.main,
           name="Info_Supplier", daemon=False)
t.start()

# ── ZMQ initialization ──────────────────────────────
# connection
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(SOCKET_STR)
print(f"Connection started with {IP_ADDRESS}")
# send request and recive 3 packets (see documentation)
socket.send(read_timestamp())
message1 = socket.recv()
message2 = socket.recv()

# ── Data initialization ──────────────────────────────
# Extractin information from packets
data1 = array('i', message1[0:4])
COUNT = data1[0]

data1 = array('d', message1[4:])
TimeStamp = data1[0]
TimeStamp -= double(0.5)

print(f"\nRecived data {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)}")
if COUNT == 1:
    data2 = array('d', message2[0:48])
    dt = data2[1]

    data2 = array('i', message2[48:64])
    Size_Dist = data2[1]-data2[0]
    Size_Frequence = data2[3]-data2[2]

    message3 = socket.recv()
    data3 = array('f', message3)
else:
    print("   ")
    print("Script stopped --->>>  Raw data is not a valid dataset")
    sys_exit()

# Constructing data
StrainRate = reshape(data3, (Size_Frequence + 1, Size_Dist + 1))

# Writing data
filenames = next(walk(SAVE_PATH), (None, None, []))[2]
if len(filenames) < QUEUE_DIM:
    print("Writing in the Queue")
    h5_file_write(f"{SAVE_PATH}/{str((TimeStamp))}.h5",
                  StrainRate, TimeStamp, dt)
else:
    print(
        f"Queue Full, lost {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)} data")
TimeStamp += double(0.5)
save_last_timestamp(TimeStamp)


# CONTINOUS COLLECTION
while True:

    # ZMQ REQ/REP
    socket.send(double(TimeStamp))
    message1 = socket.recv()
    message2 = socket.recv()
    message3 = socket.recv()

    # Getting information
    data2 = array('d', message2[0:48])
    dt = data2[1]

    data2 = array('i', message2[48:64])
    Size_Dist = data2[1]-data2[0]  # channels
    Size_Frequence = data2[3]-data2[2]  # frequences

    data1 = array('d', message1[4:])
    print(
        f"\nRecived data {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)}")

    if TimeStamp < data1[0]:
        TimeStamp = data1[0]
        # timestamp given is in the middle of acquisition. To take the timestamp
        # at the start we subtract (and later sum) half a second
        TimeStamp -= double(0.5)

        data3 = array('f', message3)
        StrainRate = reshape(data3, (Size_Frequence + 1, Size_Dist+1))
        filenames = next(walk(SAVE_PATH), (None, None, []))[2]
        if len(filenames) < QUEUE_DIM:
            print("Writing in the Queue")
            h5_file_write(f"{SAVE_PATH}/{str((TimeStamp))}.h5",
                          StrainRate, TimeStamp, dt)
        else:
            print(
                f"Queue Full, lost {datetime.fromtimestamp(TimeStamp, tz=timezone.utc)} data")

        TimeStamp += double(0.5)
        save_last_timestamp(TimeStamp)
