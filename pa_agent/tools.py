from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import AgentConfig


@dataclass
class ToolResult:
    ok: bool
    output: str


@dataclass
class SafeTools:
    config: AgentConfig

    def _resolve_in_workspace(self, path: str | Path) -> Path:
        base = self.config.workspace.resolve()
        target = (base / Path(path)).resolve()
        if target != base and base not in target.parents:
            raise ValueError(f"Path outside workspace is blocked: {target}")
        return target

    def read_file(self, path: str, max_chars: int = 8000) -> ToolResult:
        try:
            target = self._resolve_in_workspace(path)
            text = target.read_text(encoding="utf-8", errors="replace")
            return ToolResult(True, text[:max_chars])
        except Exception as e:
            return ToolResult(False, str(e))

    def write_file(self, path: str, content: str, overwrite: bool = False) -> ToolResult:
        try:
            target = self._resolve_in_workspace(path)
            if target.exists() and not overwrite:
                return ToolResult(False, f"File exists. Use --overwrite: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(True, f"Wrote {target}")
        except Exception as e:
            return ToolResult(False, str(e))

    def search_files(self, query: str) -> ToolResult:
        rg = "rg.exe" if os.name == "nt" else "rg"
        try:
            proc = subprocess.run(
                [rg, "-n", "--hidden", "--glob", "!node_modules", query],
                cwd=self.config.workspace,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            out = (proc.stdout or proc.stderr)[:12000]
            return ToolResult(proc.returncode in (0, 1), out or "No matches")
        except FileNotFoundError:
            hits: list[str] = []
            for path in self.config.workspace.rglob("*"):
                if path.is_file() and "node_modules" not in path.parts:
                    try:
                        text = path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if query.lower() in text.lower():
                        hits.append(str(path.relative_to(self.config.workspace)))
                if len(hits) >= 100:
                    break
            return ToolResult(True, "\n".join(hits) or "No matches")
        except Exception as e:
            return ToolResult(False, str(e))

    def run_shell(self, command: str) -> ToolResult:
        decision = self._shell_allowed(command)
        if decision is not None:
            return ToolResult(False, decision)
        try:
            proc = subprocess.run(
                command,
                cwd=self.config.workspace,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            output = (proc.stdout + proc.stderr).strip()
            return ToolResult(proc.returncode == 0, output[:16000])
        except subprocess.TimeoutExpired:
            return ToolResult(False, f"Command timed out after {self.config.timeout_seconds}s")
        except Exception as e:
            return ToolResult(False, str(e))

    def _shell_allowed(self, command: str) -> str | None:
        lowered = command.lower()
        for pattern in self.config.blocked_shell_patterns:
            if pattern.lower() in lowered:
                return f"Blocked by safety pattern: {pattern}"

        try:
            parts = shlex.split(command, posix=os.name != "nt")
        except ValueError:
            parts = command.split()
        if not parts:
            return "Empty command"

        exe = Path(parts[0]).name.lower()
        exe = exe[:-4] if exe.endswith(".exe") else exe
        allowed = {cmd.lower() for cmd in self.config.allowed_shell_commands}
        if exe not in allowed:
            return (
                f"Command `{exe}` is not in allowed_shell_commands. "
                "Edit agent.config.json if you trust it."
            )
        return None
