import zmq
import config_manager

context_client = zmq.Context()
socket_client = context_client.socket(zmq.REP)
config = config_manager.yaml_read("config.yaml")


context_blackbox = zmq.Context()
socket_blackbox = context_blackbox.socket(
    zmq.DEALER)  # zmq.REQ

# bind(tcp://0.0.0.0:5555) connect(172.17.64.1)
socket_client.bind(config_manager.str_constructor(config))
print("connected to client")
socket_blackbox.connect(config_manager.str_constructor(config, "server"))
print("connected to blackbox")
try:
    print("listening")

    message = socket_client.recv()
    print(
        f"Received {(message)}, now forwarding to blackbox")

    socket_blackbox.send(message)
    print("listening to msg")

    message0 = socket_blackbox.recv()
    print(f"Recived {message0}")

    message1 = socket_blackbox.recv()
    print(f"Recived {message1}")

    message2 = socket_blackbox.recv()
    print(f"Recived {message2}")

    # clean message2

    print(f"Sending Client {message2}")

    socket_client.send((message2))
    print("Sent!")
finally:
    socket_client.close()
    context_client.term()
