
import os, platform, getpass, os

def collect():
    try:
        username = getpass.getuser()
    except Exception:
        username = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    try:
        is_admin = False
        if os.name == "nt":
            # Windows: check admin via SID or via ctypes (omitted for simplicity)
            is_admin = os.environ.get("USERNAME", "").lower() == "administrator"
        else:
            is_admin = (os.geteuid() == 0)
        privilege = "admin/root" if is_admin else "normal"
    except Exception:
        privilege = "normal"
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "username": username,
        "privilege": privilege,
        "pid": os.getpid()
    }
