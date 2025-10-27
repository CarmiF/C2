
def short_id(uuid_str: str) -> str:
    return uuid_str[:8] if uuid_str else "unknown"
