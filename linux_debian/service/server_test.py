import zmq
import config_manager

context = zmq.Context()
socket = context.socket(zmq.REP)
config = config_manager.yaml_read("config.yaml")

# bind(tcp://0.0.0.0:5555) connect(172.17.64.1)
socket.bind(config_manager.str_constructor(config))

message = socket.recv_string()
print(f"Received {message}")

print("Sending 'Hello'")
socket.send_string("Hello")

socket.close()
context.term()
