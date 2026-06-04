# IMPORT
import numpy as np
import zmq
import time
import array
import sys
from timestamp_manager import read_timestamp, save_last_timestamp
import netcdf4_h5_manager

SAVE_PATH = "/data/"

# ZMQ INITIALIZATION
# ZMQ connection
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://ip_address:port")  # TO FILL #####
# ZMQ REQ/REP
socket.send(read_timestamp())
message1 = socket.recv()
message2 = socket.recv()


# DATA INITIALIZATION
# Getting information
DATA1 = array.array('i', message1[0:4])
COUNT = DATA1[0]
# DATA1 = array.array('d', message1[4::])
DATA1 = array.array('d', message1[4:])
TimeStamp = DATA1[0]
if COUNT == 1:
    DATA2 = array.array('d', message2[0:48])
    # Spacing_Dist = DATA2[0]
    # Spacing_Frequence = DATA2[1]/1000
    # Origin_Dist = DATA2[3]
    DATA2 = array.array('i', message2[48:64])
    Size_Dist = DATA2[1]-DATA2[0]
    Size_Frequence = DATA2[3]-DATA2[2]
    message3 = socket.recv()
    DATA3 = array.array('f', message3)
else:
    print("   ")
    print("Script stopped --->>>  Raw data is not a valid dataset")
    sys.exit()
# Constructing data
StrainRate = np.reshape(DATA3, (Size_Frequence + 1, Size_Dist + 1))
# Distance = (np.arange(0, Size_Dist) * Spacing_Dist + Origin_Dist)/1000
# Frequence = np.arange(0, Size_Frequence)*Spacing_Frequence
netcdf4_h5_manager.h5_file_write(
    f"{SAVE_PATH}{str(int(TimeStamp))}", StrainRate, TimeStamp)
save_last_timestamp(TimeStamp)

i = 0
# CONTINOUS COLLECTION
while i < 10:
    time.sleep(0.4)
    # ZMQ REQ/REP
    socket.send(np.double(TimeStamp))
    message1 = socket.recv()
    message2 = socket.recv()
    message3 = socket.recv()

    # Getting information
    DATA2 = array.array('d', message2[0:48])
    # Spacing_Dist = DATA2[0]
    # Spacing_Frequence = DATA2[1]/1000
    # Origin_Dist = DATA2[3]
    DATA2 = array.array('i', message2[48:64])
    Size_Dist = DATA2[1]-DATA2[0]
    Size_Frequence = DATA2[3]-DATA2[2]
    # DATA1 = array.array('d', message1[4::])
    DATA1 = array.array('d', message1[4:])
    if TimeStamp < DATA1[0]:
        i += 1
        TimeStamp = DATA1[0]
        DATA3 = array.array('f', message3)
        StrainRate = np.reshape(DATA3, (Size_Frequence + 1, Size_Dist+1))
        netcdf4_h5_manager.h5_file_write(
            f"{SAVE_PATH}{str(int(TimeStamp))}", StrainRate, TimeStamp)
        save_last_timestamp(TimeStamp)
