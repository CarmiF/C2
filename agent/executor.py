import subprocess
import shlex
import os

def run_command(cmd: str):
    # Run a system command and return its stdout, stderr, and exit code.
    #
    # Args:
    #   cmd (str): The command to execute as a string, e.g. "ls -la" or "ipconfig".
    #
    # Returns:
    #   (stdout, stderr, returncode):
    #       stdout (str): Standard output of the command.
    #       stderr (str): Standard error (error messages, if any).
    #       returncode (int): Exit code (0 = success, non-zero = failure).

    try:
        # Decide whether to use the shell based on the operating system.
        # On Windows (os.name == "nt"), using the shell is often required for
        # commands to behave as expected (cmd.exe / powershell semantics).
        # On POSIX systems (Linux/macOS), it's usually safer to avoid the shell.
        use_shell = os.name == "nt"

        if use_shell:
            # WINDOWS PATH:
            #   - cmd is passed as a single string to the system shell.
            #   - shell=True tells subprocess to run the command through cmd.exe.
            #   - capture_output=True captures both stdout and stderr.
            #   - text=True decodes the output to str instead of bytes.
            completed = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            # POSIX PATH (Linux / macOS):
            #   - We avoid shell=True for better security and predictability.
            #   - shlex.split(cmd) safely splits the command string into a list
            #     of arguments, e.g. "ls -la /tmp" -> ["ls", "-la", "/tmp"].
            #   - The command is then executed directly without an intermediate shell.
            completed = subprocess.run(shlex.split(cmd), capture_output=True, text=True)

        # completed is a subprocess.CompletedProcess object.
        #   completed.stdout: captured standard output (str)
        #   completed.stderr: captured standard error (str)
        #   completed.returncode: exit status of the process (int)
        return completed.stdout, completed.stderr, completed.returncode

    except Exception as e:
        # If an exception occurs (invalid command, OS error, etc.),
        # we return:
        #   - empty stdout,
        #   - the exception message as stderr,
        #   - and a generic non-zero return code (1) to indicate failure.
        return "", str(e), 1
