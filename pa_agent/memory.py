from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class MemoryStore:
    root: Path

    @property
    def tasks_path(self) -> Path:
        return self.root / "tasks.json"

    @property
    def notes_path(self) -> Path:
        return self.root / "notes.md"

    @property
    def profile_path(self) -> Path:
        return self.root / "profile.md"

    @property
    def research_dir(self) -> Path:
        return self.root / "research"

    def init(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.research_dir.mkdir(parents=True, exist_ok=True)
        if not self.tasks_path.exists():
            self.tasks_path.write_text("[]\n", encoding="utf-8")
        if not self.notes_path.exists():
            self.notes_path.write_text("# Notes\n\n", encoding="utf-8")
        if not self.profile_path.exists():
            self.profile_path.write_text(
                "# Profile\n\n- Main goals: research, coding, deployment learning.\n",
                encoding="utf-8",
            )

    def load_tasks(self) -> list[dict]:
        self.init()
        return json.loads(self.tasks_path.read_text(encoding="utf-8"))

    def save_tasks(self, tasks: list[dict]) -> None:
        self.init()
        self.tasks_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

    def add_task(self, text: str, project: str | None = None) -> dict:
        tasks = self.load_tasks()
        task = {
            "id": (max([t.get("id", 0) for t in tasks], default=0) + 1),
            "text": text,
            "project": project,
            "status": "open",
            "created_at": now_iso(),
            "done_at": None,
        }
        tasks.append(task)
        self.save_tasks(tasks)
        return task

    def complete_task(self, task_id: int) -> bool:
        tasks = self.load_tasks()
        changed = False
        for task in tasks:
            if int(task.get("id", -1)) == task_id:
                task["status"] = "done"
                task["done_at"] = now_iso()
                changed = True
        self.save_tasks(tasks)
        return changed

    def add_note(self, text: str) -> None:
        self.init()
        with self.notes_path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {now_iso()}\n\n{text.strip()}\n")

    def search_notes(self, query: str) -> list[str]:
        self.init()
        q = query.lower()
        hits: list[str] = []
        for line in self.notes_path.read_text(encoding="utf-8").splitlines():
            if q in line.lower():
                hits.append(line)
        return hits

    def context_summary(self) -> str:
        self.init()
        tasks = self.load_tasks()
        open_tasks = [t for t in tasks if t.get("status") == "open"][:10]
        profile = self.profile_path.read_text(encoding="utf-8")[:1200]
        task_lines = "\n".join(
            f"- #{t['id']} {t['text']} ({t.get('project') or 'general'})"
            for t in open_tasks
        )
        return f"{profile}\n\nOpen tasks:\n{task_lines or '- none'}\n"

    def save_research(self, slug: str, content: str) -> Path:
        self.init()
        safe_slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug)
        safe_slug = safe_slug.strip("-")[:80] or "research"
        path = self.research_dir / f"{datetime.now():%Y%m%d-%H%M%S}-{safe_slug}.md"
        path.write_text(content, encoding="utf-8")
        return path
