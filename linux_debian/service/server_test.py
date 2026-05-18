import zmq
import config_manager

context_client = zmq.Context()
socket_client = context_client.socket(zmq.REP)
config = config_manager.yaml_read("config.yaml")
# non aspetta messaggi in sospeso alla chiusura
# socket_client.setsockopt(zmq.LINGER, 0)


context_blackbox = zmq.Context()
socket_blackbox = context_blackbox.socket(
    zmq.REQ)  # mettere nelle opzioni il multiple

# bind(tcp://0.0.0.0:5555) connect(172.17.64.1)
socket_client.bind(config_manager.str_constructor(config))
print("connected to client")
socket_blackbox.connect(config_manager.str_constructor(config, "server"))
print("connected to blackbox")
try:
    print("listening")

    message = socket_client.recv_string()
    print(f"Received {message}, now forwarding to blackbox")

    socket_blackbox.send_string(message)
    print("listening to msg")

    message = socket_blackbox.recv_multipart()

    print(f"Recived {message[0]}")
    print(f"Recived {message[1]}")
    print(f"Recived {message[2]}")

    print(f"Sending Client {message[2]}")

    socket_client.send_string((str(message[2])))
    print("Sent!")
finally:
    socket_client.close()
    context_client.term()
