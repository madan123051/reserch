import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pa_agent.config import AgentConfig
from pa_agent.memory import MemoryStore
from pa_agent.tools import SafeTools


def main() -> int:
    with TemporaryDirectory() as d:
        root = Path(d)
        memory = MemoryStore(root / "memory")
        task = memory.add_task("ship personal agent", "agent")
        assert task["id"] == 1
        assert memory.complete_task(1)
        assert memory.load_tasks()[0]["status"] == "done"

        cfg = AgentConfig(workspace=root, memory_dir=root / "memory")
        tools = SafeTools(cfg)
        write = tools.write_file("notes/test.txt", "hello")
        assert write.ok, write.output
        assert (root / "notes" / "test.txt").read_text() == "hello"

        blocked = tools.run_shell("powershell Write-Output nope")
        assert not blocked.ok
        assert "not in allowed_shell_commands" in blocked.output

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
