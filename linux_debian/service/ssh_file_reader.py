from os import replace, remove, mkdir
from shutil import copyfile
from time import sleep
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from config_manager import yaml_read, yaml_write_dict
from netcdf4_h5_manager import read_attribute
import paramiko

CONFIG_DICT = yaml_read("config.yaml")

PORT = CONFIG_DICT["socket_ssh"]["port"]
IP_ADDRESS = CONFIG_DICT["socket_ssh"]["ip"]
USERNAME = CONFIG_DICT["credentials"]["user"]
PASSWORD = CONFIG_DICT["credentials"]["passwd"]
SERVER_PATH = CONFIG_DICT["paths"]["server_data_dir"]
SAVE_PATH = CONFIG_DICT["paths"]["save_path"]
CONFIG_PATH = CONFIG_DICT["paths"]["info_dir"]
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


def info_dict(path: str) -> dict:
    """Read a .h5 file from the passed variable path.
    Return a dictionary with the info with key from the config and value 
    from the read file."""
    return_dict = {}
    with Dataset(path, mode="r") as file_read:
        for info in SUPP_INFO:
            value = read_attribute(file_read, info)
            if value is not None:
                return_dict[info] = value
    return return_dict


def check_connection(client_instance) -> bool:
    """Check if the connection with client_instance is still active. Return a bool"""
    try:
        transport = client_instance.get_transport()
        if transport is None or not transport.is_active():
            raise EOFError
        transport.send_ignore()
        return True
    except (EOFError, OSError, paramiko.ssh_exception.SSHException):
        return False


def main() -> None:
    """Connect to the acquisition machine and download a complete file every minute. 
    Check if something changed. If it did, let the file in the directory to be downloaded"""
    try:
        client_session, sftp_session = connect(
            IP_ADDRESS, PORT, USERNAME, PASSWORD)
    except paramiko.SSHException:
        print(f"Can't connect to {IP_ADDRESS}")

    # ── mkdir to store the downloaded files ──────────────────────────────
    try:
        mkdir(CONFIG_PATH)
    except FileExistsError:
        pass

    while True:
        try:
            list_file = file_list_from_path(sftp_session, SERVER_PATH)
            list_file.sort(reverse=True)
            if len(list_file) == 0:
                sleep(1)
                continue
            last_file = list_file[0]
            sftp_session.get(f"{SERVER_PATH}/{last_file}",
                             f"{CONFIG_PATH}/{last_file}")
        except (IOError, paramiko.SSHException):
            if not check_connection(client_session):
                try:
                    sftp_session.close()
                    client_session.close()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                client_session, sftp_session = connect(
                    IP_ADDRESS, PORT, USERNAME, PASSWORD)

        supplement_data = info_dict(f"{CONFIG_PATH}/{last_file}")
        if supplement_data != yaml_read(f"{CONFIG_PATH}/_add_info.yaml"):
            yaml_write_dict(supplement_data, f"{CONFIG_PATH}/_add_info.yaml")
            copyfile(f"{CONFIG_PATH}/_add_info.yaml",
                     f"{CONFIG_PATH}/_tmp_copy.yaml")
            replace(f"{CONFIG_PATH}/_tmp_copy.yaml",
                    f"{SAVE_PATH}/_add_info.yaml")
        remove(f"{CONFIG_PATH}/{last_file}")
        sleep(59)


if __name__ == "__main__":
    main()
