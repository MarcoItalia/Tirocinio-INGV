import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.bind("tcp://0.0.0.0:5555")

message = "Hello"
print(f"Sending {message}..")


socket.send_string(message)
print(socket.recv_string())

socket.close()
context.term()
