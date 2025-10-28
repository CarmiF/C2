import datetime
SESSION_START_TIME = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

LOGS_DIRECTORY = f"logs/{SESSION_START_TIME}"
MAIN_LOG_FILE = f"{LOGS_DIRECTORY}/general_server_log"
HOST = "0.0.0.0"
PORT = 9001
MAX_CONNECTIONS_BACKLOG = 100
RECV_BUFFER = 4096
