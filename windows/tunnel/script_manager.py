import time
import paramiko


def is_script_running(ssh, script_name):
    """Look for the script_name (path)"""

    _, stdout, _ = ssh.exec_command(f"pgrep -f {script_name}")
    return stdout.read().strip() != b""


def start_script(ssh, script_path):
    """Start the python script named passed in script_path (path)"""

    try:
        _, out, err = ssh.exec_command(
            f'nohup python3 "{script_path}" > /tmp/script.log 2>&1 & echo $!'
        )
        pid = out.read().decode().strip()
        err_out = err.read().decode().strip()
        print(f"PID lanciato: {pid}")
        print(f"Stderr: {err_out}")

        time.sleep(2)

        print("Script avviato")
    except Exception as e:
        print(f"Exception -> {e}")
