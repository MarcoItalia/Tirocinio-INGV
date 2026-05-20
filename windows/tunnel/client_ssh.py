import paramiko
import script_manager
import timestamp_manager
import dict_to_namespace as dtns
import json
import time


host = "172.17.69.255"
username = "marco"
password = "marco"
path = "/mnt/c/users/marco/Documenti/Università/III Anno/Tirocinio"
working_dir = f"{path}/linux_debian/service/"
path_local = "C:/Users/marco/Documents/Università/III Anno/Tirocinio/prova_copia"

client = paramiko.client.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=username, password=password)
sftp_session = client.open_sftp()

last_timestamp = timestamp_manager.read_timestamp()

print(last_timestamp)
print(f"1 {sftp_session.getcwd()}")
print(f"2 {sftp_session.chdir(path)}")
print(f"3 {sftp_session.getcwd()}")
print(f"4 {path_local}")


try:
    files = sftp_session.listdir(
        "/mnt/c/users/marco/Documenti/Università/III Anno/Tirocinio/prova_da_copiare")
    numbers = [int(f.replace(".txt", "")) for f in files if f.endswith(".txt")]
    minimo = min(numbers)

    if minimo > last_timestamp:
        with sftp_session.open(f"{working_dir}timestamp.json", mode="w+", encoding="utf-8") as f:
            json.dump(vars(timestamp_manager.json_read()), f, indent=4)
except ValueError:
    pass

if not script_manager.is_script_running(client, "server_test_ssh.py"):
    print("Starting script..")
    script_manager.start_script(
        client, f"{working_dir}server_test_ssh.py")
    time.sleep(1)
else:
    print("Script already running")
i = 0
while i < 10:
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
