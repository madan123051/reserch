from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_ALLOWED_COMMANDS = [
    "git",
    "python",
    "py",
    "pytest",
    "node",
    "npm",
    "npx",
    "pnpm",
    "bun",
    "rg",
    "dir",
    "ls",
    "type",
    "cat",
    "docker",
    "vercel",
]

DEFAULT_BLOCKED_PATTERNS = [
    "rm -rf",
    "del /s",
    "format ",
    "shutdown",
    "restart-computer",
    "remove-item -recurse",
    "remove-item -force",
    "> /dev/",
]


@dataclass
class AgentConfig:
    agent_name: str = "Personal Agent"
    workspace: Path = field(default_factory=lambda: Path.cwd())
    memory_dir: Path = field(default_factory=lambda: Path.cwd() / "memory")
    allowed_shell_commands: list[str] = field(
        default_factory=lambda: list(DEFAULT_ALLOWED_COMMANDS)
    )
    blocked_shell_patterns: list[str] = field(
        default_factory=lambda: list(DEFAULT_BLOCKED_PATTERNS)
    )
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key_env: str = "OPENAI_API_KEY"
    model_env: str = "AI_MODEL"
    timeout_seconds: int = 60

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.openai_api_key_env)

    @property
    def model(self) -> str | None:
        return os.getenv(self.model_env)


def load_config(path: Path | None = None) -> AgentConfig:
    config_path = path or Path("agent.config.json")
    if not config_path.exists():
        cfg = AgentConfig()
        cfg.memory_dir = cfg.workspace / "memory"
        return cfg

    raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    workspace = Path(raw.get("workspace", ".")).expanduser().resolve()
    memory_dir = Path(raw.get("memory_dir", workspace / "memory")).expanduser()
    if not memory_dir.is_absolute():
        memory_dir = workspace / memory_dir

    return AgentConfig(
        agent_name=raw.get("agent_name", "Personal Agent"),
        workspace=workspace,
        memory_dir=memory_dir.resolve(),
        allowed_shell_commands=raw.get(
            "allowed_shell_commands", list(DEFAULT_ALLOWED_COMMANDS)
        ),
        blocked_shell_patterns=raw.get(
            "blocked_shell_patterns", list(DEFAULT_BLOCKED_PATTERNS)
        ),
        openai_base_url=raw.get("openai_base_url", "https://api.openai.com/v1"),
        openai_api_key_env=raw.get("openai_api_key_env", "OPENAI_API_KEY"),
        model_env=raw.get("model_env", "AI_MODEL"),
        timeout_seconds=int(raw.get("timeout_seconds", 60)),
    )


def write_default_config(path: Path) -> None:
    data = {
        "agent_name": "Madan Personal Agent",
        "workspace": ".",
        "memory_dir": "memory",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_api_key_env": "OPENAI_API_KEY",
        "model_env": "AI_MODEL",
        "timeout_seconds": 60,
        "allowed_shell_commands": DEFAULT_ALLOWED_COMMANDS,
        "blocked_shell_patterns": DEFAULT_BLOCKED_PATTERNS,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
