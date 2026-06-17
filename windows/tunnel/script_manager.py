import time
import paramiko


def is_script_running(ssh, script_name):
    """Look for the script_name (path)"""

    _, stdout, _ = ssh.exec_command(f"pgrep -f {script_name}")
    return stdout.read().strip() != b""


def pid_script(ssh, script_name) -> int:
    """If the script is running, return is pid. Else 0"""

    if is_script_running(ssh, script_name):
        _, stdout, _ = ssh.exec_command(f"pgrep -f {script_name}")
        return int(stdout.read().strip())

    return 0


def script_kill(ssh, script):
    """Kill the script which the pid or name is passed. Accept as script int or str"""
    if type(script) is int:
        pass
    elif type(script) is str:
        script = pid_script(ssh, script)
    else:
        raise TypeError("Only integers and str are allowed")
    ssh.exec_command(f"kill {script}")


def start_script(ssh, script_path):
    """Start the python script named passed in script_path (path)"""

    try:
        _, out, err = ssh.exec_command(
            f'nohup python3 "{script_path}" > /tmp/script.log 2>&1 & echo $!'
        )
    except Exception as e:
        print(f"Exception -> {e}")
