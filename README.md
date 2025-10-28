# C2 — Minimal C2 (client/server)

A minimal, educational Command-and-Control (C2) example implemented in Python. The repository contains a small TCP JSON protocol, a server that maintains an in-memory agent registry and a simple REPL, and an agent that performs a handshake and executes commands on request.

## Setup Instructions

1. Ensure Python 3.10 or newer is installed.
2. Clone the repository into a new, dedicated folder.
3. Navigate into the newly cloned repository folder 
4. Move one level up to the directory that contains the repository folder.

## Instructions for Running the Server and Client

### Run the server
Open a terminal and run:

Windows: 
```bash
python -m C2.server.main
```
Linux:
```bash
python3 -m C2.server.main
```
The server listens on `0.0.0.0:9001` by default. Use the REPL to issue commands:
- `list` — list connected agents
- `exec <agent_id> <command>` — request agent to execute `<command>`
- `quit` — stop the server REPL (the server thread will terminate on process exit)

### Run the agent (client)
Open a second terminal and run the agent, pointing it at the server IP and port:

Windows: 
```bash
python -m C2.agent.main --host 127.0.0.1 --port 9001
```
Linux:
```bash
python3 -m C2.agent.main --host 127.0.0.1 --port 9001
```
Replace `127.0.0.1` and `9001` with the server address and port used in your environment.

## Description of the Protocol

Messages are JSON objects sent over TCP using a 4-byte big-endian length prefix (unsigned int) framing. The top-level JSON object must be a mapping with at least a `type` key.

Defined message types:
- `handshake` — sent by agent to server immediately after connection.
  - payload: agent metadata (fields include `id`, `addr`, `hostname`, `os`, `username`, `privilege`, `pid`)
- `exec` — sent by server to agent to request execution.
  - payload: `{ "cmd": "<shell command>" }`
- `exec_result` — sent by agent to server as a response to `exec`.
  - payload: `{ "stdout": "<stdout str>", "stderr": "<stderr str>", "code": <int> }`

Length-prefix framing ensures that message boundaries are preserved regardless of TCP segmentation. The repository implements `send_message(sock, obj)` and `recv_message(sock)` helpers in `C2/server/transport.py`.

Security note: This implementation is intentionally minimal and lacks authentication, encryption, and hardening. Do not deploy on untrusted networks without adding TLS, strong authentication, and process isolation.

## Overview of Optional Features Implemented

This repository focuses on the minimal, vital functionality. Optional or convenience features implemented:

- Simple REPL on the server to list agents and send `exec` commands.
- Length-prefixed JSON framing for robust message boundaries.
- Minimal in-memory `SessionRegistry` to manage connected agents.
- Stable agent identifier generated per connection (UUID).

## Files of interest

- `C2/server/main.py` — server entrypoint and REPL
- `C2/server/transport.py` — framing and JSON send/receive helpers
- `C2/server/protocol.py` — message constructors and type predicates
- `C2/server/session.py` — in-memory registry of agents
- `C2/agent/main.py` — agent entrypoint and main loop
- `C2/agent/executor.py` — command execution helper
- `C2/agent/sysinfo.py` — system information collector used in handshake

