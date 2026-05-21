import paramiko
import script_manager
import timestamp_manager
import dict_to_namespace as dtns
import json
import time
import config_manager

config = config_manager.yaml_read("config.yaml")
host = config.socket.ip
username = config.credentials.user
password = config.credentials.passwd
path = config.paths.path_server
working_dir = f"{path}/linux_debian/service/"
path_local = config.paths.path_local
# "C:/Users/marco/Documents/Università/III Anno/Tirocinio/prova_copia"

# connect
try:
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    # open sftp session, it opens automatically a tunnelled conn
    sftp_session = client.open_sftp()
except Exception as e:
    print(f"Cannot connect, exception: {e}")

last_timestamp = timestamp_manager.read_timestamp()


# check if script run
running = script_manager.is_script_running(
    client, "server_test_ssh.py")

# read timestamp server so i could align client and server ts if needed
try:
    with sftp_session.open(f"{working_dir}timestamp.json", mode="r") as f:
        timestamp_server = dtns.dict_to_namespace(json.load(f))
except Exception as e:
    print(f"Exception: {e}")

    # if the server ts > client ts check if the data is there to be read.
if timestamp_server.last_timestamp > last_timestamp:
    files = sftp_session.listdir(f"{path}/prova_da_copiare")

    # when file name change and format change, this need to be updated!
    numbers = [int(f.replace(".txt", "")) for f in files if f.endswith(".txt")]

    try:

        minim = min(numbers)
        # when file name change and format change, this need to be updated!

    except ValueError:  # in case there are non or i can't read the file as numbers, i assume the worst case
        minim = timestamp_server.last_timestamp

    if minim > last_timestamp:

        if running:  # how to solve concurrency? Kill the other concurrent process
            script_manager.script_kill(client, "server_test_ssh.py")
            running = False

        # align the timestamps
        with sftp_session.open(f"{working_dir}timestamp.json", mode="w+") as f:
            json.dump(vars(timestamp_manager.json_read()), f, indent=4)

elif timestamp_server.last_timestamp < last_timestamp:

    if running:
        script_manager.script_kill(client, "server_test_ssh.py")
        running = False

    with sftp_session.open(f"{working_dir}timestamp.json", mode="w+") as f:
        json.dump(vars(timestamp_manager.json_read()), f, indent=4)


if not running:
    script_manager.start_script(client, f"{working_dir}/server_test_ssh.py")

time.sleep(2)

failed_before = False

i = 0
while i < 10:  # while true
    try:
        sftp_session.get(f"{path}/prova_da_copiare/{str(last_timestamp)}.txt",
                         f"{path_local}/{str(last_timestamp)}.txt")
        last_timestamp += 1
        i += 1
        timestamp_manager.save_last_timestamp(last_timestamp)
        sftp_session.remove(
            f"{path}/prova_da_copiare/{str(last_timestamp - 1)}.txt")
        if failed_before:
            time.sleep(5)
        else:
            time.sleep(1)

    except IOError:
        failed_before = True
        time.sleep(1)
    except Exception as e:
        print(f"Errore: {e}")
        break

sftp_session.close()
client.close()
