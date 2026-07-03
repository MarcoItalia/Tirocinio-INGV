from os import rename, mkdir, remove
from time import sleep
from threading import Thread
from numpy import double
from yaml_manager import yaml_read
import paramiko
import netcdf_stitch
import script_manager

# ── Config reader ──────────────────────────────

config = yaml_read("config.yaml")

FILE_EXT = config["extension"]
HOST = config["socket"]["ip"]
PORT = config["socket"]["port"]
USERNAME = config["credentials"]["user"]
PASSWORD = config["credentials"]["passwd"]
PATH_SERVER = config["paths"]["path_server"]
PATH_LOCAL = config["paths"]["path_local"]
SERVER_DIR_NAME = config["paths"]["server_save_dir"]
SCRIPT_NAME = config["server_script_name"]
INFO_PATH = config["paths"]["info_dir"]
ADD_INFO_FILE_NAME = "_add_info.yaml"

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
    If the list has no elements, then return it. If the list as just one element and have not yet failed,
    that means that this element has been already checked (last iteration had 2 element and was returned as a list of
    this singular item), the function "increment" the name as it was a double and return that new file.
    Parameters
    ----------
    list_last_timestamp: list
        list of files that rapresent the files to check.
        It's the output of file_list_from_path or up_file or [].
    fails: int
        number of times the current file has been checked and was not found.
        Only when the last file as not yet failed it needs to be incremented.
    """
    if len(list_last_timestamp) > 1:
        print("Reading from list")
        return list_last_timestamp[1:]
    if len(list_last_timestamp) == 0:
        return []
    # increment
    if fails == 0:
        pos_ext = list_last_timestamp[0].find(FILE_EXT)
        if pos_ext != -1:  # extension has been found
            file_name = list_last_timestamp[0]
            print(f"Incrementing {file_name}")
            list_last_timestamp[0] = str(
                double(file_name[:pos_ext])+1)+file_name[pos_ext:]
        else:
            return []

    return list_last_timestamp


def create_dir(path_dir: str):
    """
    Create a dir from the passed parameter
    Parameters
    ----------
    path_dir: str
        absolute path.
    """
    try:
        mkdir(path_dir)
    except FileExistsError:
        pass


def get_next_file(sftp_session, path: str, list_last_timestamp, fails) -> list:
    """
    Return a list of ordered files from which the first element is the next
    that need to be downloaded.
    It reset the list reading the dir if the list is empty or if it failed too many times.
    Parameters
    ----------
    path: str
        absolute path. The function will pass this to file_list_from_path in theoffchance it need to read the directory.
    list_last_timestamp: list
        list of files that rapresent the files to check.
        It's the output of file_list_from_path or up_file or [].
    fails: int
        number of fails to find a file.
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
    """Connect to a remote machine via ssh and download .h5 in a specified dir using sftp.
    If you download a .yaml file, the program put that in another dir.
    Start a script in the remote machine to take the data (.h5 files) from the acquisition machine
    Start a thread to "stitch" the .h5 file together and use the .yaml file to add the missing information.
    """
    # ── Connect using the function ──────────────────────────────
    try:
        client, sftp_session = connect(HOST, PORT, USERNAME, PASSWORD)
    except Exception as e:
        # if error, just print it and end the program
        print(f"Cannot connect, exception: {e}")
        exit(-1)

    # ── Check if the script in the connected machine is running ───────────────
    if not script_manager.is_script_running(client, SCRIPT_NAME):
        print(f"Starting script at {PATH_SERVER}/{SCRIPT_NAME}")
        script_manager.start_script(client, f"{PATH_SERVER}/{SCRIPT_NAME}")
        sleep(1.5)  # sleep because of the connection delay

    # ── mkdir to store the downloaded and info files ──────────────────────────────

    create_dir(PATH_LOCAL)

    create_dir(INFO_PATH)

    # ── Start a thread to stitch the downloaded file ──────────────────────────────

    t = Thread(target=netcdf_stitch.main,
               name="Stitch", daemon=True)
    t.start()

    # ── Download all the file in the directory ──────────────────────────────

    first_add_file = True
    file_list = []
    consecutive_fails = 0

    while True:
        # ── Check the connection and the script ──────────────────────────────
        if consecutive_fails >= 60:

            print("Checking if the connection is still up")
            try:
                transport = client.get_transport()
                if transport is None or not transport.is_active():
                    raise paramiko.SSHException
                transport.send_ignore()
                print("Connection Running")
            except (EOFError, OSError, paramiko.SSHException):
                try:
                    print("Connection lost, restarting..")
                    try:
                        sftp_session.close()
                        client.close()
                    except Exception:  # pylint: disable=broad-exception-caught
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

            file_list = []

        if first_add_file:
            try:
                sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{ADD_INFO_FILE_NAME}",
                                 f"{INFO_PATH}/_temp_download_info")
                try:
                    rename(f"{INFO_PATH}/_temp_download_info",
                           f"{INFO_PATH}/{ADD_INFO_FILE_NAME}")
                except WindowsError:
                    remove(f"{INFO_PATH}/{ADD_INFO_FILE_NAME}")
                    rename(f"{INFO_PATH}/_temp_download_info",
                           f"{INFO_PATH}/{ADD_INFO_FILE_NAME}")
                sftp_session.remove(
                    f"{PATH_SERVER}/{SERVER_DIR_NAME}/{ADD_INFO_FILE_NAME}")
                first_add_file = False
                print(f"\nRead {ADD_INFO_FILE_NAME}")
            except FileNotFoundError:
                pass

        try:

            file_list = get_next_file(sftp_session,
                                      f"{PATH_SERVER}/{SERVER_DIR_NAME}/", file_list, consecutive_fails)

            # check if the list is []. It can happens when we download (or start
            # the script by program) too fast that the list of files in the dir is still empty.
            if len(file_list) == 0:
                consecutive_fails += 1
                print(f"\nList empty\n Fail number: {consecutive_fails}")
                continue

            # check if the file is a .h5 file
            extension = (file_list[0]).find(FILE_EXT)
            if extension == -1:

                # check if the file is a .yaml file
                extension = (file_list[0]).find(".yaml")
                if extension != -1:
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
                    print(f"\nRead {file_list[0]}")
                    first_add_file = False
                    continue
                consecutive_fails += 1
                continue

            # ── Download the files and rename it ──────────────────────────────
            # Rename is guranteed atomic, meanwhile get isn't if the file is too big.
            sftp_session.get(f"{PATH_SERVER}/{SERVER_DIR_NAME}/{file_list[0]}",
                             f"{PATH_LOCAL}/_temp_download_file")
            rename(f"{PATH_LOCAL}/_temp_download_file",
                   f"{PATH_LOCAL}/{file_list[0]}")

            print(f"\nRead {file_list[0]}")
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
