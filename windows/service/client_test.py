import zmq
import config_manager
import timestamp_manager
import numpy as np

context = zmq.Context()
socket = context.socket(zmq.REQ)
config = config_manager.yaml_read("config.yaml")

socket.connect(config_manager.str_constructor(config))

try:
    message = timestamp_manager.last_timestamp_read("timestamp.json")
    print(f"Sending {np.double(message)}..")

    socket.send(np.double(message))

    print("listening for reply..")

    print(socket.recv())
    timestamp_manager.last_timestamp_increment("timestamp.json")
finally:
    socket.close()
    context.term()
