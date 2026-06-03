import paramiko
import script_manager
import timestamp_manager
import time
import config_manager
import sys

config = config_manager.yaml_read("config.yaml")
host = config.socket.ip
username = config.credentials.user
password = config.credentials.passwd
path = config.paths.path_server
working_dir = f"{path}/linux_debian/service/"
path_local = config.paths.path_local


def list_file(path_to_list):
    sftp_session.chdir(path_to_list)
    files = sftp_session.listdir()
    return [f for f in files]


def up_file(file_name: str):
    extension = file_name.find(".txt")
    file_name = str(int(file_name[0:extension])+1)+file_name[extension:]
    return file_name


def get_next_file(path, last_timestamp, consecutive_fails):
    """Decide which file to download"""
    if last_timestamp is None or consecutive_fails >= 2:
        # first esecution or too much fails → list dir
        files = list_file(f"{path}/prova_da_copiare")
        if files != []:
            print(f"Using list reading {files[0]}")
            return files[0]
        else:
            return None
        # return files[0] if files else None
    else:
        print(f"Using upfile reading {up_file(last_timestamp)}")
        return up_file(last_timestamp)


# connect
try:
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    # open sftp session, it opens automatically a tunnelled conn
    sftp_session = client.open_sftp()
except Exception as e:
    print(f"Cannot connect, exception: {e}")
    sys.exit(-1)

# check if script run
if not script_manager.is_script_running(
        client, "server_test_ssh.py"):
    script_manager.start_script(client, f"{working_dir}/server_test_ssh.py")


# read timestamp server so i could align client and server ts if needed

last_timestamp = None
consecutive_fails = 0
i = 0

while i < 10:
    last_timestamp = get_next_file(path, last_timestamp, consecutive_fails)

    if last_timestamp is None:
        time.sleep(1)
        continue

    try:
        sftp_session.get(f"{path}/prova_da_copiare/{last_timestamp}",
                         f"{path_local}/{last_timestamp}")
        print(f"Read {last_timestamp}")
        consecutive_fails = 0
        i += 1
        timestamp_manager.save_last_timestamp(last_timestamp)
        sftp_session.remove(f"{path}/prova_da_copiare/{last_timestamp}")
        time.sleep(0.5)

    except IOError:
        consecutive_fails += 1
        print("Fallimento")
        time.sleep(1)
    except Exception as e:
        print(f"Errore: {e}")
        break

sftp_session.close()
client.close()
