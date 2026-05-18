import zmq
import config_manager
import timestamp_manager

context = zmq.Context()
socket = context.socket(zmq.REQ)
config = config_manager.yaml_read("config.yaml")

socket.connect(config_manager.str_constructor(config))
# str(config.socket.protocol) + "://" + str(config.socket.ip) + ":" + str(config.socket.port)
try:
    message = timestamp_manager.last_timestamp_read("timestamp.json")
    print(f"Sending {message}..")

    socket.send_string(str(message))

    print("listening for reply..")

    print(socket.recv_string())
    timestamp_manager.last_timestamp_increment("timestamp.json")
finally:
    socket.close()
    context.term()
