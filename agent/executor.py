
import subprocess
import shlex
import os

def run_command(cmd: str):
    try:
        # Use shell for Windows compatibility, but prefer exec with shlex on POSIX
        use_shell = os.name == "nt"
        if use_shell:
            completed = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            completed = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
        return completed.stdout, completed.stderr, completed.returncode
    except Exception as e:
        return "", str(e), 1
