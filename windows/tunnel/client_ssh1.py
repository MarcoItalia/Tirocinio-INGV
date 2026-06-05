from numpy import double
from sys import exit
from os import rename
import paramiko
import time
import script_manager
import timestamp_manager
import config_manager


config = config_manager.yaml_read("config.yaml")

FILE_EXT = config.extension
HOST = config.socket.ip
USERNAME = config.credentials.user
PASSWORD = config.credentials.passwd
PATH_SERVER = f"{config.paths.path_server}"
PATH_LOCAL = config.paths.path_local
SERVER_DIR_NAME = config.paths.server_save_dir
SCRIPT_NAME = config.server_script_name


def list_file(path_to_list) -> list:
    """Get the file list from the connected machine"""
    sftp_session.chdir(path_to_list)
    files = sftp_session.listdir()
    return [f for f in files]


def up_file(list_last_timestamp, consecutive_fails) -> list:
    """Get a list and the number of fails. Return a list that start with the next file to search"""
    if len(list_last_timestamp) > 1:
        print("Using list")
        return list_last_timestamp[1:]
    if len(list_last_timestamp) == 0:
        return []

    if consecutive_fails == 0:
        extension = list_last_timestamp[0].find(FILE_EXT)
        file_name = list_last_timestamp[0]
        print(f"Incrementing {file_name}")
        list_last_timestamp[0] = str(
            int(file_name[:extension])+1)+file_name[extension:]
    print(list_last_timestamp[0])
    return list_last_timestamp


def get_next_file(path, last_timestamp, consecutive_fails) -> list:
    """Decide which file to download"""
    if len(last_timestamp) == 0 or consecutive_fails >= 2:
        # first esecution or too much fails → list dir
        files = list_file(f"{path}")
        if files != []:
            print(f"Inizializing file list..  {files}")
            files.sort()
            return files
        else:
            return []
    else:
        return up_file(last_timestamp, consecutive_fails)


# connect
try:
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USERNAME, password=PASSWORD)
    # open sftp session, it opens automatically a tunnelled conn
    sftp_session = client.open_sftp()
except Exception as e:
    print(f"Cannot connect, exception: {e}")
    exit(-1)

# check if script run
if not script_manager.is_script_running(
        client, "server_test_ssh.py"):
    print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
    script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
time.sleep(1)
print(script_manager.is_script_running(
    client, SCRIPT_NAME))

last_timestamp = []
consecutive_fails = 0
i = 0

while i < 10:
    last_timestamp = get_next_file(
        f"{PATH_SERVER}/{SERVER_DIR_NAME}/", last_timestamp, consecutive_fails)

    if len(last_timestamp) == 0:
        continue

    try:
        extension = (last_timestamp[0]).find(FILE_EXT)
        file_name = str(last_timestamp[0])[:extension]
        sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{last_timestamp[0]}",
                         f"{PATH_LOCAL}/{file_name}")

        rename(f"{PATH_LOCAL}/{file_name}",
               f"{PATH_LOCAL}/{last_timestamp[0]}")

        print(f"Read {last_timestamp[0]}")
        consecutive_fails = 0
        i += 1
        timestamp_manager.save_last_timestamp(double(file_name))
        sftp_session.remove(
            f"{PATH_SERVER}/{SERVER_DIR_NAME}/{last_timestamp[0]}")
        time.sleep(0.5)  # should remove it

    except IOError:
        consecutive_fails += 1
        print("Fallimento")
        time.sleep(0.4)
    except Exception as e:
        print(f"Errore: {e}")
        break

sftp_session.close()
client.close()
