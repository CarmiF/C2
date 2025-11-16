import os, platform, getpass, os
# os       : interact with the operating system (env vars, PID, user IDs, etc.).
# platform : get information about the underlying OS (name, version, hostname, etc.).
# getpass  : safely get the current user's login name.
# os       : imported again (duplicate import, harmless but redundant).


def collect():
    # Collect basic runtime information about the current machine and process.
    # Returns a dictionary containing:
    #   - hostname  : machine name in the network/OS
    #   - os        : operating system name and version
    #   - username  : current user running this process
    #   - privilege : "admin/root" if running with elevated privileges, otherwise "normal"
    #   - pid       : current process ID

    try:
        # Primary method: use getpass.getuser() to retrieve the current username.
        # This usually respects the login name on most platforms.
        username = getpass.getuser()
    except Exception:
        # Fallback: if getpass.getuser() fails (for example in some restricted or
        # non-standard environments), try to read the username from environment
        # variables commonly used on different systems:
        #   - "USERNAME" (Windows)
        #   - "USER"     (Linux/macOS)
        # If neither is set, default to "unknown".
        username = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"

    try:
        # Default assumption: not running as admin/root.
        is_admin = False

        if os.name == "nt":
            # Windows path:
            # os.name == "nt" indicates Windows (NT family: Windows 10, 11, etc.).
            #
            # Proper admin detection on Windows is usually done by checking:
            #   - security identifiers (SIDs),
            #   - or using ctypes to call Windows APIs.
            # Here, for simplicity, we just check if the username is literally
            # "administrator", which is a naive but simple heuristic.
            is_admin = os.environ.get("USERNAME", "").lower() == "administrator"
        else:
            # POSIX path (Linux / macOS):
            # os.geteuid() returns the effective user ID of the current process.
            # On Unix-like systems:
            #   - UID 0 == root (full admin privileges).
            # Therefore, if geteuid() == 0, the process is running as root.
            is_admin = (os.geteuid() == 0)

        # Map the boolean is_admin flag to a human-readable privilege label:
        #   - "admin/root" if running with elevated privileges
        #   - "normal"     otherwise
        privilege = "admin/root" if is_admin else "normal"
    except Exception:
        # If anything goes wrong while checking privileges (e.g. os.geteuid()
        # not available, environment issues, etc.), fall back to assuming
        # normal privileges.
        privilege = "normal"

    # Build and return a dictionary with all collected information.
    return {
        # platform.node() typically returns the system's network name / hostname,
        # e.g. "DESKTOP-1234AB", "carmi-laptop", "server-01".
        "hostname": platform.node(),

        # platform.system()  -> OS name, e.g. "Windows", "Linux", "Darwin" (macOS).
        # platform.release() -> OS release / version, e.g. "10", "5.15.0-92-generic".
        # Combined into a single string like "Windows 10" or "Linux 5.15.0-92-generic".
        "os": f"{platform.system()} {platform.release()}",

        # The username determined above (either via getpass.getuser(),
        # environment variables, or "unknown" as a last resort).
        "username": username,

        # Privilege level string based on whether the process appears to run
        # as admin/root or not.
        "privilege": privilege,

        # os.getpid() returns the current process ID (an integer).
        # This uniquely identifies the running process in the OS process table.
        "pid": os.getpid()
    }
