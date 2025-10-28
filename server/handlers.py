
from typing import Optional
from C2.server.protocol import TYPE_EXEC_RESULT
from C2.server.session import SessionRegistry, AgentEntry

def handle_incoming(registry: SessionRegistry, agent: AgentEntry, msg: dict, logger) -> Optional[str]:
    t = msg.get("type")
    if t == TYPE_EXEC_RESULT:
        p = msg.get("payload", {})
        exit_code = p.get("exit_code")
        stdout = p.get("stdout", "")
        stderr = p.get("stderr", "")
        logger.info("Exec result from %s: exit=%s stdout_len=%d stderr_len=%d",
                    agent.short, exit_code, len(stdout), len(stderr))
        # Return a human-friendly string for optional CLI display
        return f"[{agent.short}] exit={exit_code} stdout_len={len(stdout)} stderr_len={len(stderr)}"
    # Default: enqueue raw
    return None
