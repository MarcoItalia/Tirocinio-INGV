from os import mkdir, walk
from sys import exit as sys_exit
from threading import Thread
from time import sleep
from datetime import datetime, timezone
from array import array
from numpy import reshape, double
from netcdf4_h5_manager import h5_file_write
from timestamp_manager import read_timestamp, save_last_timestamp
from yaml_manager import yaml_read
import ssh_file_reader
import zmq


# ── Config reader ──────────────────────────────
config = yaml_read("config.yaml")

SAVE_PATH = config["paths"]["save_path"]
PORT = config["socket_zmq"]["port"]
IP_ADDRESS = config["socket_zmq"]["ip"]
PROTOCOL = config["socket_zmq"]["protocol"]
QUEUE_DIM = config["paths"]["queue_dim"]
SOCKET_STR = f"{PROTOCOL}://{IP_ADDRESS}:{PORT}"


def write_packet(timestamp, strain_rate, dt):
    """Write a StrainRate packet to disk, respecting the queue size limit."""
    filenames = next(walk(SAVE_PATH), (None, None, []))[2]
    if len(filenames) < QUEUE_DIM:
        print("Writing in the Queue")
        h5_file_write(f"{SAVE_PATH}/{str(timestamp)}.h5",
                      strain_rate, timestamp, dt)
    else:
        print(
            f"Queue Full, lost {datetime.fromtimestamp(timestamp, tz=timezone.utc)} data")


class ZmqDc:
    """
    Wraps a ZMQ REQ socket connected to the acquisition server.
    Handles the request/reply exchange and automatically reconnects
    if a send/recv times out.
    """

    def __init__(self):
        self.create_socket()

    def create_socket(self):
        """Create and connect a fresh REQ socket with timeouts set."""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.SNDTIMEO, 500)
        self.socket.setsockopt(zmq.RCVTIMEO, 2000)
        self.socket.setsockopt(zmq.REQ_RELAXED, 1)
        self.socket.setsockopt(zmq.REQ_CORRELATE, 1)
        self.socket.connect(SOCKET_STR)
        print(f"Connection started with {IP_ADDRESS}")

    def comunicate(self, timestamp):
        """
        Send a request for the given timestamp and receive the reply.
        Always recives 2 packets(message1, message2); a 3rd packet
        (message3) is only received if message1 reports COUNT == 1
        (a valid dataset). If COUNT != 1, raises ValueError.
        If a send/recv times out(zmq.Again), the socket is recreated
        and the same request is retried from scratch.
        Parameters:
        ----------
        timestamp: double
            timestamp of the last file read        
        """
        while True:
            try:
                self.socket.send(timestamp)
                msg1 = self.socket.recv()
                msg2 = self.socket.recv()
                data = array('i', msg1[0:4])
                count = data[0]
                if count == 1:
                    msg3 = self.socket.recv()
                    return msg1, msg2, msg3
                else:
                    raise ValueError
            except zmq.Again:
                print("Connection lost, reconnecting...")
                self.create_socket()
                sleep(0.25)


def main() -> None:
    """
    Entry point of the acquisition client.

    Starts a background thread (ssh_file_reader) that downloads
    additional data from the acquisition server, then opens a ZMQ REQ
    connection to it and continuously requests StrainRate packets 
    starting from the last saved timestamp. (Note that if the timestamp is too old,
    the server reply with the most recent. This behaviour is intended)

    Each received packet is written to disk as an HDF5 file (respecting
    the configured queue size limit) and the timestamp is persisted to
    disk so the script can resume from where it left off if restarted.
    The loop never returns; it exits only via sys_exit() if the server
    reports an invalid dataset (COUNT != 1).
    """
    # ── mkdir to store the downloaded files ──────────────────────────────
    try:
        mkdir(SAVE_PATH)
    except FileExistsError:
        pass

    # ── Start a thread to download complete file and read add info ──────────────────────────────

    t = Thread(target=ssh_file_reader.main,
               name="Info_Supplier", daemon=True)
    t.start()

    # ── ZMQ initialization ──────────────────────────────
    # connection
    zmq_collector = ZmqDc()

    # initialization
    first_time = True
    timestamp = read_timestamp()
    # send request and recive 3 packets (see documentation)
    while True:
        try:
            message1, message2, message3 = zmq_collector.comunicate(timestamp)
        except ValueError:
            print("\nScript stopped --->>>  Raw data is not a valid dataset")
            sys_exit()

        # ── Data initialization ──────────────────────────────
        # Extractin information from packets

        data1 = array('d', message1[4:])
        if (timestamp < data1[0]) or first_time:
            timestamp = data1[0]
            timestamp -= double(0.5)
            first_time = False

            print(
                f"\nRecived data {datetime.fromtimestamp(timestamp, tz=timezone.utc)}")

            data2 = array('d', message2[0:48])
            dt = data2[1]
            data2 = array('i', message2[48:64])
            size_dist = data2[1]-data2[0]
            size_frequence = data2[3]-data2[2]

            data3 = array('f', message3)

            # Constructing data
            StrainRate = reshape(data3, (size_frequence + 1, size_dist + 1))
            # Saving Packet
            write_packet(timestamp, StrainRate, dt)

            timestamp += double(0.5)
            save_last_timestamp(timestamp)
        else:
            # no new data yet, avoid busy-looping
            sleep(0.15)


if __name__ == "__main__":
    main()
