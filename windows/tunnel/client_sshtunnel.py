import paramiko
import time
import timestamp_manager
import os

# Update the next three lines with your
# server's information


def connect_ssh(hostname, port, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port,
                username=username, password=password)
    return ssh


def is_script_running(ssh, script_name):
    _, stdout, _ = ssh.exec_command(f"pgrep -f {script_name}")
    return stdout.read().strip() != b""


def start_script(ssh, script_path):
    ssh.exec_command(f"python3 {script_path} &")

    # da config.yaml in seguito
host = "172.17.69.255"
port = 22
username = "marco"
password = "marco"

remote_dir = "/path/dati/"
script_name = "acquisizione.py"
script_path = f"/path/{script_name}"
local_dir = "./dati/"
sleep_time = 10  # secondi

ssh_client = connect_ssh(host, port, username, password)
sftp = ssh_client.open_sftp()

# step 2 - controlla/avvia script acquisizione
if not is_script_running(ssh_client, script_name):
    start_script(ssh_client, script_path)
    time.sleep(2)  # aspetta che si avvii

    # carica ultimo timestamp salvato
last_timestamp = timestamp_manager.read_timestamp()

sftp.chdir(remote_dir)  # step 3

while True:
    # step 4-5 - scarica file nuovi
    files = sftp.listdir()
    new_files = [
        f for f in files if timestamp_manager.is_newer(f, last_timestamp)]

    for file in sorted(new_files):
        local_path = os.path.join(local_dir, file)
        sftp.get(file, local_path)
        sftp.remove(file)  # elimina dopo il download
        last_timestamp = timestamp_manager.extract_timestamp(file)
        timestamp_manager.save_last_timestamp(last_timestamp)

    time.sleep(sleep_time)  # step 6
