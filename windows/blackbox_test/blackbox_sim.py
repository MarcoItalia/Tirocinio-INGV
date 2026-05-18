import zmq

context = zmq.Context()
socket = context.socket(zmq.ROUTER)  # zmq.REP
context.setsockopt(zmq.ROUTER_MANDATORY, True)

socket.bind("tcp://0.0.0.0:5000")

try:
    # message = socket.recv()
    # print(f"Received {message}")

    message = socket.recv_multipart()
    print(f"Received {message}")

    socket.send_multipart([message[0], b"msg1"])
    socket.send_multipart([message[0], b"msg2"])
    socket.send_multipart([message[0], b"msg3"])
    # socket.send(b"msg2")
    # socket.send(b"msg3")

    # print("Sending 'msg1'")
    # socket.send_string("msg1")
    # print("Sending 'msg2'")
    # socket.send_string("msg2")
    # print("Sending 'msg3'")
    # socket.send_multipart([b"msg1", b"msg2", b"msg3"])
finally:
    socket.close()
    context.term()
