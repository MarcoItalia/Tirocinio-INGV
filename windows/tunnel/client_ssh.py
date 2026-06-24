from os import rename, mkdir, remove
from time import sleep
from threading import Thread
from numpy import double
from config_manager import yaml_read
import paramiko
import netcdf_stitch
import script_manager

# ── Config reader ──────────────────────────────

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
INFO_PATH = config.paths.info_dir + "/" + "_add_info.yaml"


# ── Support functions ──────────────────────────────

def file_list_from_path(sftp_session, path_to_list: str = None) -> list:
    """
    Read a directory from the connected machine and return the list of file in the directory
    If a directory is passed, then read that. If None is passed, then read the current directory
    Parameters
    ----------
    path_to_list: string
        absolute path. The function will change the dir working dir to that and than return a list
        of all the files.
    """
    if path_to_list is not None:
        sftp_session.chdir(path_to_list)
    files = sftp_session.listdir()
    return [f for f in files]


def up_file(list_last_timestamp, fails) -> list:
    """
    Check if the passed list as other elements. If it's True, than return the list minus the first element.
    If the list has no elements, then return it. If the list as just one element and have not yet failed, that
    means that this element has been already checked (last iteration had 2 element and was returned as a list of
    this singular item), the function "increment" the name as it was a double and return that new file.
    Parameters
    ----------
    list_last_timestamp: list
        list of files that rapresent the files to check. It's the output of file_list_from_path or up_file or [].
    fails: int
        number of times the current file has been checked and was not found. This is relevant because only the first fail
        the last file in the list is incremented. Incrementing each time will means just a waste of computation.        
    """
    if len(list_last_timestamp) > 1:
        print("Reading from list")
        return list_last_timestamp[1:]
    if len(list_last_timestamp) == 0:
        return []
    # increment
    if fails == 0:
        pos_ext = list_last_timestamp[0].find(FILE_EXT)
        if pos_ext != -1:
            file_name = list_last_timestamp[0]
            print(f"Incrementing {file_name}")
            list_last_timestamp[0] = str(
                double(file_name[:pos_ext])+1)+file_name[pos_ext:]
        else:
            return []

    # print(list_last_timestamp[0])
    return list_last_timestamp


def get_next_file(sftp_session, path: str, list_last_timestamp, fails) -> list:
    """
    Return a list of ordered files from which the first element is the next
    that need to be downloaded. 
    It reset the list reading the working directory if the list is empty or if the download failed too many times.
    Parameters
    ----------
    path: str
        absolute path. The function will pass this to file_list_from_path in theoffchance it need to read the directory.
    list_last_timestamp: list
        list of files that rapresent the files to check. It's the output of file_list_from_path or up_file or [].
    fails: int
        number of fails to find a specific file.
    """
    # check if reset is needed
    if len(list_last_timestamp) == 0 or fails >= 2:
        files = file_list_from_path(sftp_session, f"{path}")
        if files != []:
            print(f"Inizializing file list..  {files}")
            files.sort()
            return files
        else:
            return []
    # return the next to read
    else:
        return up_file(list_last_timestamp, fails)


def connect(host_ip, host_port, usarname: str, password: str):
    """
    Create a ssh connection using paramiko. 
    Return SSHClient and open_sftp, in this order.
    Parameters
    ----------
    host_ip: str
        string representing the host ip
    host_port: int
        number of the port to connect
    username: str
        the username to authenticate as
    password: str
        used for password authentication
    """
    client_con = paramiko.client.SSHClient()
    client_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client_con.connect(host_ip, port=host_port,
                       username=usarname, password=password)
    # open sftp session, it opens automatically a tunnelled conn
    sftp_session_con = client_con.open_sftp()
    return client_con, sftp_session_con


def main() -> None:

    # ── Connect using the function ──────────────────────────────
    try:
        client, sftp_session = connect(HOST, PORT, USERNAME, PASSWORD)
    except Exception as e:
        # if error, just print it and end the program
        print(f"Cannot connect, exception: {e}")
        exit(-1)

    # ── Check if the script in the connected machine is running ──────────────────────────────
    if not script_manager.is_script_running(client, SCRIPT_NAME):
        print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
        script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
        sleep(1.5)  # sleep because of the delay

    # ── mkdir to store the downloaded files ──────────────────────────────

    try:
        mkdir(PATH_LOCAL)
    except FileExistsError:
        pass

    # ── Start a thread to stitch the downloaded file ──────────────────────────────

    t = Thread(target=netcdf_stitch.main,
               name="Stitch", daemon=False)
    t.start()

    # ── Download all the file in the directory ──────────────────────────────

    file_list = []
    consecutive_fails = 0

    while True:
        # ── Check the connection and the script ──────────────────────────────
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
                    client, sftp_session = connect(
                        HOST, PORT, USERNAME, PASSWORD)
                    consecutive_fails = 0
                    print("Connection restarted")
                except Exception as e:
                    print(f"Cannot connect, exception: {e}")
                    exit(-1)

            print("Checking if the script is still running")
            if not script_manager.is_script_running(client, SCRIPT_NAME):
                print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
                script_manager.start_script(
                    client, f"{PATH_SERVER}/{SCRIPT_NAME}")
                consecutive_fails = 0
                sleep(1.5)
            # because 0mq doesn't have an innate and easy mode to check the connection, SCRIPT_NAME doesn't have a contingency
            # in case the connection drop. This is the easiest and laziest way to just reset the connection
            elif consecutive_fails >= 400:
                script_manager.script_kill(
                    client, f"{PATH_SERVER}/{SCRIPT_NAME}")
                sleep(0.2)
                script_manager.start_script(
                    client, f"{PATH_SERVER}/{SCRIPT_NAME}")
                consecutive_fails = 0
                sleep(1.5)

            file_list = []

        try:

            file_list = get_next_file(sftp_session,
                                      f"{PATH_SERVER}/{SERVER_DIR_NAME}/", file_list, consecutive_fails)

            # check if the list is []. It can happens when we download (or start the script by program)
            # too fast that the list of files in the dir is still empty.
            if len(file_list) == 0:
                consecutive_fails += 1
                print(f"Fail number: {consecutive_fails}")
                continue

            # check if the file is a .h5 file
            extension = (file_list[0]).find(FILE_EXT)
            if extension == -1:

                # check if the file is a .yaml file
                extension = (file_list[0]).find(".yaml")
                if extension == -1:
                    # if it is, download it. Don't update consecutive_fails
                    sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}",
                                     f"{INFO_PATH}/_temp_download_info")
                    try:
                        rename(f"{INFO_PATH}/_temp_download_info",
                               f"{INFO_PATH}/{file_list[0]}")
                    except WindowsError:
                        remove(f"{INFO_PATH}/{file_list[0]}")
                        rename(f"{INFO_PATH}/_temp_download_info",
                               f"{INFO_PATH}/{file_list[0]}")
                    sftp_session.remove(
                        f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}")
                    continue
                consecutive_fails += 1
                continue

            # ── Download the files and rename it ──────────────────────────────
            # Rename is guranteed atomic, meanwhile get isn't if the file is too big.
            sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}",
                             f"{PATH_LOCAL}/_temp_download_file")
            rename(f"{PATH_LOCAL}/_temp_download_file",
                   f"{PATH_LOCAL}/{file_list[0]}")

            print(f"Read {file_list[0]}")
            consecutive_fails = 0

            # after the download we remove it to not download it again.
            sftp_session.remove(
                f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}")

        # all of these exception can happens and mean the same thing:
        # reading error, the file you are reading doesnt exist. Increment the fail count.
        except (IOError, OSError, paramiko.ssh_exception.SSHException):
            consecutive_fails += 1
            print(f"Fail number: {consecutive_fails}")
            sleep(0.3)
        except Exception as e:
            print(f"Errore: {e}")
            break

    sftp_session.close()
    client.close()


if __name__ == "__main__":
    main()
