import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5555")

print("Waiting for msg...")

message = socket.recv_string()
print(f"Received request: {message}")
socket.send_string("World")

socket.close()
context.term()
