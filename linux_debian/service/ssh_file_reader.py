from os import replace, remove, mkdir
from types import SimpleNamespace
from time import sleep
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from config_manager import yaml_read, yaml_write_dict
from netcdf4_h5_manager import read_attribute
import paramiko

config = yaml_read("config.yaml")

PORT = config.socket_ssh.port
IP_ADDRESS = config.socket_ssh.ip
USERNAME = config.credentials.user
PASSWORD = config.credentials.passwd
SERVER_PATH = config.data_dir.server_data_dir
SAVE_PATH = config.data_dir.save_path
CONFIG_PATH = config.data_dir.config_dir
SUPP_INFO = config.supplement_attribute


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
    return_dict = {}
    for info in SUPP_INFO:
        with Dataset(path, mode="r") as file_read:
            info_value = read_attribute(file_read, info)
        return_dict.update({info: info_value})
    return return_dict


def main() -> None:
    client_session, sftp_session = connect(
        IP_ADDRESS, PORT, USERNAME, PASSWORD)

    # ── mkdir to store the downloaded files ──────────────────────────────
    try:
        mkdir(CONFIG_PATH)
    except FileExistsError:
        pass

    while True:
        # check conn
        list_file = file_list_from_path(sftp_session, SERVER_PATH)
        last_file = list_file.sort(reverse=True)[0]
        sftp_session.get(f"{SERVER_PATH}/{last_file}",
                         f"{CONFIG_PATH}/{last_file}")

        supplement_data = info_dict(f"{CONFIG_PATH}/{last_file}")

        yaml_write_dict(supplement_data, f"{CONFIG_PATH}/_temp_info")
        replace(f"{CONFIG_PATH}/_temp_info",
                f"{SAVE_PATH}/_add_info.yaml")
        remove(f"{CONFIG_PATH}/{last_file}")
        sleep(59)


if __name__ == "__main__":
    main()
