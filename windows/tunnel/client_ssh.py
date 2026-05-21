import paramiko
import script_manager
import timestamp_manager
import dict_to_namespace as dtns
import json
import time


host = "172.17.69.255"
username = "marco"
password = "marco"
path = "/mnt/c/users/marco/Documents/Università/III Anno/Tirocinio"
working_dir = f"{path}/linux_debian/service/"
path_local = "C:/Users/marco/Documents/Università/III Anno/Tirocinio/prova_copia"

# connect
client = paramiko.client.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=username, password=password)
# open sftp session, it opens automatically a tunnelled conn
sftp_session = client.open_sftp()

last_timestamp = timestamp_manager.read_timestamp()

print(last_timestamp)
print(f"1 {sftp_session.getcwd()}")
print(f"2 {sftp_session.chdir(path)}")
print(f"3 {sftp_session.getcwd()}")
print(f"4 {path_local}")

# check if script run
running = script_manager.is_script_running(
    client, "server_test_ssh.py")

time.sleep(3)

_, stdout, _ = client.exec_command("cat /tmp/script.log")
print(stdout.read().decode())

# read timestamp server and keep the file open because i could align client and server ts
print("Opening timestamp server")
try:
    with sftp_session.open(f"{working_dir}timestamp.json", mode="r") as f:
        timestamp_server = dtns.dict_to_namespace(json.load(f))
        print(timestamp_server)
except Exception as e:
    print(f"Exception: {e}")

    # if the server ts > client ts check if the data is there to be read.
if timestamp_server.last_timestamp > last_timestamp:
    print("checking if the data is there..")
    files = sftp_session.listdir(f"{path}/prova_da_copiare")
    numbers = [int(f.replace(".txt", "")) for f in files if f.endswith(".txt")]
    try:
        minim = min(numbers)
    except ValueError:
        minim = timestamp_server.last_timestamp
    if minim > last_timestamp:
        print(f"2.1 {minim} > {last_timestamp}")
        if running:
            script_manager.script_kill(client, "server_test_ssh.py")
            running = False
        with sftp_session.open(f"{working_dir}timestamp.json", mode="w+") as f:
            json.dump(vars(timestamp_manager.json_read()), f, indent=4)
elif timestamp_server.last_timestamp < last_timestamp:
    print(f"2.2 {timestamp_server.last_timestamp} < {last_timestamp}")
    if running:
        script_manager.script_kill(client, "server_test_ssh.py")
        running = False
    with sftp_session.open(f"{working_dir}timestamp.json", mode="w+") as f:
        json.dump(vars(timestamp_manager.json_read()), f, indent=4)


if not running:
    script_manager.start_script(client, f"{working_dir}/server_test_ssh.py")

time.sleep(3)
_, stdout, _ = client.exec_command("cat /tmp/script.log")
print(stdout.read().decode())

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
        time.sleep(1)
    except IOError:
        time.sleep(2)
    except Exception as e:
        print(f"Errore: {e}")
        break

sftp_session.close()
client.close()
