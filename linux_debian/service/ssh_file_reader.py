from os import replace, remove, mkdir
from shutil import copyfile
from time import sleep
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from yaml_manager import yaml_read, yaml_write_dict
from netcdf4_h5_manager import read_attribute
import paramiko

CONFIG_DICT = yaml_read("config.yaml")

PORT = CONFIG_DICT["socket_ssh"]["port"]
IP_ADDRESS = CONFIG_DICT["socket_ssh"]["ip"]
USERNAME = CONFIG_DICT["credentials"]["user"]
PASSWORD = CONFIG_DICT["credentials"]["passwd"]
SERVER_PATH = CONFIG_DICT["paths"]["server_data_dir"]
SAVE_PATH = CONFIG_DICT["paths"]["save_path"]
ADD_INFO_PATH = CONFIG_DICT["paths"]["info_dir"]
SUPP_INFO = CONFIG_DICT["supplement_attribute"]


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


def extract_info_dict(path: str) -> dict:
    """
    Read a .h5 file from the passed variable path.
    Return a dictionary with the info with key from the config and value 
    from the read file.
    Parameters
    ----------
    path: str
        string with the complete path of the .h5 file to read attribute from
    """
    return_dict = {}
    with Dataset(path, mode="r") as file_read:
        for info in SUPP_INFO:
            value = read_attribute(file_read, info)
            if value is not None:
                return_dict[info] = value
    return return_dict


def check_connection(client_instance) -> bool:
    """
    Check if the connection with client_instance is still active. Return a bool
    Parameters
    ----------
    client_instance: 
        client session. First result of connect()
    """
    try:
        transport = client_instance.get_transport()
        if transport is None or not transport.is_active():
            raise EOFError
        transport.send_ignore()
        return True
    except (EOFError, OSError, paramiko.ssh_exception.SSHException):
        return False


def main() -> None:
    """
    Connect to the acquisition machine and download a complete file every minute. 
    Check if something changed. If it did, let the yaml with the
    new info be downloaded in the directory
    """
    # ── Connect to the acquisition machine ──────────────────────────────
    try:
        client_session, sftp_session = connect(
            IP_ADDRESS, PORT, USERNAME, PASSWORD)
    except paramiko.SSHException:
        print(f"Can't connect to {IP_ADDRESS}")

    # ── mkdir to store the downloaded files ──────────────────────────────
    try:
        mkdir(ADD_INFO_PATH)
    except FileExistsError:
        pass

    # ── Start continuous acquisition ──────────────────────────────
    while True:
        # ── Get the file from the directory ──────────────────────────────
        try:
            list_file = file_list_from_path(sftp_session, SERVER_PATH)
            if len(list_file) == 0:  # if there isn't one, just retry after 1 second
                sleep(1)
                continue
            list_file.sort(reverse=True)
            last_file = list_file[0]  # if there is, take the last file
            sftp_session.get(f"{SERVER_PATH}/{last_file}",
                             f"{ADD_INFO_PATH}/{last_file}")
        # if you get a connection error, check the connection
        except (IOError, paramiko.SSHException):
            if not check_connection(client_session):
                try:
                    sftp_session.close()
                    client_session.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                client_session, sftp_session = connect(
                    IP_ADDRESS, PORT, USERNAME, PASSWORD)

        # ── Extract info and save them. Leave a copy in memory for future check ──────────────────────────

        supplement_data = extract_info_dict(f"{ADD_INFO_PATH}/{last_file}")
        try:
            if supplement_data != yaml_read(f"{ADD_INFO_PATH}/_add_info.yaml"):
                yaml_write_dict(supplement_data,
                                f"{ADD_INFO_PATH}/_add_info.yaml")
                copyfile(f"{ADD_INFO_PATH}/_add_info.yaml",
                         f"{ADD_INFO_PATH}/_tmp_copy.yaml")
                replace(f"{ADD_INFO_PATH}/_tmp_copy.yaml",
                        f"{SAVE_PATH}/_add_info.yaml")
        # the not found refer to _add_info.yaml, because all the other are created here and
        # really not accessed from someone/something else. Basically, if it's the first time
        # _add_info.yaml is not yet there, so it's saved
        except FileNotFoundError:
            yaml_write_dict(supplement_data, f"{ADD_INFO_PATH}/_add_info.yaml")
            copyfile(f"{ADD_INFO_PATH}/_add_info.yaml",
                     f"{ADD_INFO_PATH}/_tmp_copy.yaml")
            replace(f"{ADD_INFO_PATH}/_tmp_copy.yaml",
                    f"{SAVE_PATH}/_add_info.yaml")
        remove(f"{ADD_INFO_PATH}/{last_file}")
        sleep(59)


if __name__ == "__main__":
    main()
