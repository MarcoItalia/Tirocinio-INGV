import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://172.17.64.1:5555")

print("Sending 'Hello'")
socket.send_string("Hello")

message = socket.recv_string()
print(f"Received reply {message}")

socket.close()
context.term()
