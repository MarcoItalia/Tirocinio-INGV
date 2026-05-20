import paramiko
from pathlib import Path
import script_manager
import time
command = "df"


def is_script_running(ssh, script_name):
    _, stdout, _ = ssh.exec_command(f"pgrep -f {script_name}")
    return stdout.read().strip() != b""


def start_script(ssh, script_path):
    try:
        _, out, err = ssh.exec_command(
            f'nohup python3 "{path}/linux_debian/service/server_test_donothing.py" > /tmp/script.log 2>&1 & echo $!'
        )
        pid = out.read().decode().strip()
        err_out = err.read().decode().strip()
        print(f"PID lanciato: {pid}")
        print(f"Stderr: {err_out}")

        time.sleep(2)

        print("Script avviato")
    except Exception as e:
        print(f"Exception -> {e}")

# Update the next three lines with your
# server's information


host = "172.17.69.255"
username = "marco"
password = "marco"
path = "/mnt/c/users/marco/Documenti/Università/III Anno/Tirocinio"
path_local = "C:/Users/marco/Documents/Università/III Anno/Tirocinio/prova_copia"
client = paramiko.client.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=username, password=password)
sftp_session = client.open_sftp()

print(f"1 {sftp_session.getcwd()}")
print(f"2 {sftp_session.chdir(path)}")
print(f"3 {sftp_session.getcwd()}")
print(f"4 {path_local}")


if not is_script_running(client, "server_test_donothing.py"):
    print("Starting script..")
    start_script(
        client, f"{path}/linux_debian/service/server_test_donothing.py")
    time.sleep(2)  # aspetta che si avvii
else:
    print("Script already running")


try:
    sftp_session.get(
        f"{path}/prova_da_copiare/README.md", f"{path_local}/README.md")
except Exception as e:
    print(f"Errore: {e}")

# _stdin, _stdout, _stderr = client.exec_command(command)
# print(_stdout.read().decode())
sftp_session.close()
client.close()
