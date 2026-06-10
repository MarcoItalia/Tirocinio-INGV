from numpy import double
from os import rename, mkdir
from time import sleep
import paramiko
import script_manager
import timestamp_manager
from config_manager import yaml_read

config = yaml_read("config.yaml")

FILE_EXT = config.extension
HOST = config.socket.ip
PORT = config.socket.port
USERNAME = config.credentials.user
PASSWORD = config.credentials.passwd
PATH_SERVER = f"{config.paths.path_server}"
PATH_LOCAL = config.paths.path_local
SERVER_DIR_NAME = config.paths.server_save_dir
SCRIPT_NAME = config.server_script_name


def file_list_from_path(path_to_list: str = None) -> list:
    """Get the file list from the connected machine"""
    if path_to_list is not None:
        sftp_session.chdir(path_to_list)
    files = sftp_session.listdir()
    return [f for f in files]


def up_file(list_last_timestamp, consecutive_fails) -> list:
    """Get a list and the number of fails. Return a list that start with the next file to search"""
    if len(list_last_timestamp) > 1:
        print("Reading from list")
        return list_last_timestamp[1:]
    if len(list_last_timestamp) == 0:
        return []

    if consecutive_fails == 0:
        pos_ext = list_last_timestamp[0].find(FILE_EXT)
        if pos_ext != -1:
            file_name = list_last_timestamp[0]
            print(f"Incrementing {file_name}")
            list_last_timestamp[0] = str(
                double(file_name[:pos_ext])+1)+file_name[pos_ext:]
    print(list_last_timestamp[0])
    return list_last_timestamp


def get_next_file(path, list_last_timestamp, consecutive_fails) -> list:
    """Decide which file to download"""
    if len(list_last_timestamp) == 0 or consecutive_fails >= 2:
        files = file_list_from_path(f"{path}")
        if files != []:
            print(f"Inizializing file list..  {files}")
            files.sort()
            return files
        else:
            return []
    else:
        return up_file(list_last_timestamp, consecutive_fails)


def connect(host_ip, host_port, usarname: str, password: str) -> paramiko.client:
    """Create a connection using paramiko. Return SSHClient and open_sftp"""
    client_con = paramiko.client.SSHClient()
    client_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_con.connect(host_ip, port=host_port,
                       username=usarname, password=password)
    # open sftp session, it opens automatically a tunnelled conn
    sftp_session_con = client_con.open_sftp()
    return client_con, sftp_session_con

    # connect


# connect
try:
    client, sftp_session = connect(HOST, PORT, USERNAME, PASSWORD)
except Exception as e:
    print(f"Cannot connect, exception: {e}")
    exit(-1)

# check if script run
if not script_manager.is_script_running(client, SCRIPT_NAME):
    print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
    script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
    sleep(1.5)

# mkdir if it doesn't exist
try:
    mkdir(PATH_LOCAL)
except FileExistsError:
    pass

file_list = []
consecutive_fails = 0

# crea dei file senza estensione!
while True:  # true
    if consecutive_fails >= 60:
        print("Checking if the connection is still up")
        try:
            transport = client.get_transport()
            if transport is None or not transport.is_active():
                raise EOFError
            transport.send_ignore()
            print("Connection Running")
        except (EOFError, OSError, paramiko.ssh_exception.SSHException):
            try:
                print("Connection lost, restarting..")
                try:
                    sftp_session.close()
                    client.close()
                except Exception:
                    pass
                client, sftp_session = connect(HOST, PORT, USERNAME, PASSWORD)
                consecutive_fails = 0
                print("Connection restarted")
            except Exception as e:
                print(f"Cannot connect, exception: {e}")
                exit(-1)
        print("Checking if the script is still running")
        if not script_manager.is_script_running(client, SCRIPT_NAME):
            print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
            script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
            consecutive_fails = 0
            sleep(1.5)
        elif consecutive_fails >= 400:
            script_manager.script_kill(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
            sleep(0.2)
            script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
            consecutive_fails = 0
            sleep(1.5)
        file_list = []
        consecutive_fails = 0

    try:

        file_list = get_next_file(
            f"{PATH_SERVER}/{SERVER_DIR_NAME}/", file_list, consecutive_fails)

        if len(file_list) == 0:
            consecutive_fails += 1
            print(f"Fail number: {consecutive_fails}")
            continue

        extension = (file_list[0]).find(FILE_EXT)
        file_name = str(file_list[0])[:extension]
        sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}",
                         f"{PATH_LOCAL}/{file_name}")

        rename(f"{PATH_LOCAL}/{file_name}",
               f"{PATH_LOCAL}/{file_list[0]}")

        print(f"Read {file_list[0]}")
        consecutive_fails = 0
        timestamp_manager.save_last_timestamp(double(file_name))
        sftp_session.remove(
            f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}")

    except (IOError, OSError, paramiko.ssh_exception.SSHException):
        consecutive_fails += 1
        print(f"Fail number: {consecutive_fails}")
        sleep(0.3)
    except Exception as e:
        print(f"Errore: {e}")
        break

sftp_session.close()
client.close()
