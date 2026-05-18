import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://0.0.0.0:5000")

try:
    message = socket.recv_string()
    print(f"Received {message}")

    print("Sending 'msg1'")
    # socket.send_string("msg1")
    print("Sending 'msg2'")
    # socket.send_string("msg2")
    print("Sending 'msg3'")
    socket.send_multipart([b"msg1", b"msg2", b"msg3"])
finally:
    socket.close()
    context.term()
