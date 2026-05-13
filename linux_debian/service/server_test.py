import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://172.17.64.1:5555")

message = socket.recv_string()
print(f"Received {message}")

print("Sending 'Hello'")
socket.send_string("Hello")

socket.close()
context.term()
