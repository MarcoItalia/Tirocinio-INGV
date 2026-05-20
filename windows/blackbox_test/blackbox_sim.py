import zmq

context = zmq.Context()
socket = context.socket(zmq.ROUTER)  # zmq.REP
context.setsockopt(zmq.ROUTER_MANDATORY, True)

socket.bind("tcp://0.0.0.0:5000")

try:

    message = socket.recv()
    print(f"Received {message}")

    socket.send_multipart([message, b"msg1"])
    socket.send_multipart([message, b"msg2"])
    socket.send_multipart([message, b"msg3"])

finally:
    socket.close()
    context.term()
