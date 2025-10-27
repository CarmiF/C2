
# Python C2 (Levels 1–3)

Lightweight, legal C2 infrastructure for red-team interview demos.

## Features
- TCP outbound agent connections
- Interactive terminal CLI
- Multiple agents, session management
- Remote command execution (stdout, stderr, exit code)
- Server and client logging
- JSON messages with 4-byte length prefix

## Project Structure
```
c2/
├─ server/
│  ├─ main.py
│  ├─ cli.py
│  ├─ session.py
│  ├─ handlers.py
│  ├─ protocol.py
│  ├─ transport.py
│  ├─ logging_conf.py
│  └─ config.py
├─ common/
│  ├─ models.py
│  ├─ errors.py
│  └─ utils.py
├─ agent/
│  ├─ main.py
│  ├─ sysinfo.py
│  ├─ executor.py
│  └─ protocol.py
└─ tests/
```

## Quickstart

Open two terminals from the project root:

### 1) Run the server
```bash
python3 -m c2.server.main
```
The server listens on `0.0.0.0:9001` by default.

### 2) Run the agent (same machine, for demo)
Edit `c2/agent/main.py` to point `SERVER_HOST` to the server IP if needed, then:
```bash
python3 -m c2.agent.main
```

### CLI usage
- `list`
- `use <short_id>`
- `send <command>`
- `broadcast <command>`
- `read <short_id>`
- `logs [n]`
- `quit`

## Notes
- Use in authorized environments only.
- No TLS in this phase; add later if needed.
- Tested with Python 3.10+.
