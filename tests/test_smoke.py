from pathlib import Path

from pa_agent.config import AgentConfig
from pa_agent.memory import MemoryStore
from pa_agent.tools import SafeTools


def test_memory_task_round_trip(tmp_path: Path) -> None:
    memory = MemoryStore(tmp_path / "memory")
    task = memory.add_task("ship personal agent", "agent")
    assert task["id"] == 1
    assert memory.complete_task(1)
    assert memory.load_tasks()[0]["status"] == "done"


def test_shell_blocks_unknown_command(tmp_path: Path) -> None:
    cfg = AgentConfig(workspace=tmp_path, memory_dir=tmp_path / "memory")
    tools = SafeTools(cfg)
    result = tools.run_shell("powershell Write-Output nope")
    assert not result.ok
    assert "not in allowed_shell_commands" in result.output


def test_file_write_stays_inside_workspace(tmp_path: Path) -> None:
    cfg = AgentConfig(workspace=tmp_path, memory_dir=tmp_path / "memory")
    tools = SafeTools(cfg)
    result = tools.write_file("notes/test.txt", "hello")
    assert result.ok
    assert (tmp_path / "notes" / "test.txt").read_text() == "hello"
