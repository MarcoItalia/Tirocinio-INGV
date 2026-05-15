import zmq
import config_manager
import timestamp_manager

context = zmq.Context()
socket = context.socket(zmq.REQ)
config = config_manager.yaml_read("config.yaml")
socket.bind(str(config.socket_client.protocol) + "://" + str(config.socket_client.ip) +
            ":" + str(config.socket_client.port))

message = timestamp_manager.json_read("timestamp.json")
print(f"Sending {message.last_timestamp}..")


socket.send_string(str(message.last_timestamp))
print(socket.recv_string())

socket.close()
context.term()
