from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .__main__ import build_runtime
from .config import write_default_config


STATIC_DIR = Path(__file__).resolve().parent / "static"


class WebApp:
    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = config_path
        if config_path:
            path = Path(config_path)
        else:
            path = Path("agent.config.json")
        if not path.exists():
            write_default_config(path)
        self.memory, self.tools, self.workflows = build_runtime(str(path))

    def status(self) -> dict:
        cfg = self.tools.config
        tasks = self.memory.load_tasks()
        open_tasks = [task for task in tasks if task.get("status") == "open"]
        return {
            "agent_name": cfg.agent_name,
            "workspace": str(cfg.workspace),
            "memory_dir": str(cfg.memory_dir),
            "model_connected": bool(cfg.api_key and cfg.model),
            "model": cfg.model,
            "open_tasks": len(open_tasks),
            "total_tasks": len(tasks),
        }


def create_handler(app: WebApp):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PersonalAgentWeb/0.1"

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("[web] " + fmt % args + "\n")

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                self.send_json(app.status())
                return
            if parsed.path == "/api/tasks":
                self.send_json({"tasks": app.memory.load_tasks()})
                return
            if parsed.path == "/api/notes":
                self.send_json(
                    {"notes": app.memory.notes_path.read_text(encoding="utf-8")}
                )
                return
            if parsed.path == "/api/search":
                query = parse_qs(parsed.query).get("q", [""])[0]
                result = app.tools.search_files(query)
                self.send_json({"ok": result.ok, "output": result.output})
                return
            self.serve_static(parsed.path)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            data = self.read_json()
            try:
                if parsed.path == "/api/chat":
                    text = str(data.get("message", "")).strip()
                    self.send_json({"output": app.workflows.general_answer(text)})
                    return
                if parsed.path == "/api/research":
                    topic = str(data.get("topic", "")).strip()
                    self.send_json({"output": app.workflows.research(topic)})
                    return
                if parsed.path == "/api/review":
                    path = str(data.get("path", ".")).strip() or "."
                    self.send_json({"output": app.workflows.code_review(path)})
                    return
                if parsed.path == "/api/deploy":
                    path = str(data.get("path", ".")).strip() or "."
                    self.send_json({"output": app.workflows.deploy_check(path)})
                    return
                if parsed.path == "/api/shell":
                    command = str(data.get("command", "")).strip()
                    result = app.tools.run_shell(command)
                    self.send_json({"ok": result.ok, "output": result.output})
                    return
                if parsed.path == "/api/tasks":
                    text = str(data.get("text", "")).strip()
                    project = data.get("project")
                    if not text:
                        self.send_json({"error": "Task text is required"}, 400)
                        return
                    task = app.memory.add_task(text, str(project) if project else None)
                    self.send_json({"task": task, "tasks": app.memory.load_tasks()})
                    return
                if parsed.path == "/api/tasks/done":
                    task_id = int(data.get("id", 0))
                    changed = app.memory.complete_task(task_id)
                    self.send_json({"ok": changed, "tasks": app.memory.load_tasks()})
                    return
                if parsed.path == "/api/notes":
                    text = str(data.get("text", "")).strip()
                    if not text:
                        self.send_json({"error": "Note text is required"}, 400)
                        return
                    app.memory.add_note(text)
                    self.send_json(
                        {"notes": app.memory.notes_path.read_text(encoding="utf-8")}
                    )
                    return
                if parsed.path == "/api/notes/search":
                    query = str(data.get("query", "")).strip()
                    self.send_json({"hits": app.memory.search_notes(query)})
                    return
            except Exception as exc:
                self.send_json({"error": str(exc)}, 500)
                return
            self.send_json({"error": "Not found"}, 404)

        def read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw or "{}")

        def send_json(self, data: dict, status: int = 200) -> None:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def serve_static(self, path: str) -> None:
            rel = "index.html" if path in {"", "/"} else path.lstrip("/")
            target = (STATIC_DIR / rel).resolve()
            if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
                self.send_error(403)
                return
            if not target.exists() or not target.is_file():
                target = STATIC_DIR / "index.html"
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="personal-agent-web")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config")
    args = parser.parse_args(argv)

    app = WebApp(args.config)
    server = ThreadingHTTPServer((args.host, args.port), create_handler(app))
    print(f"Personal Agent webapp: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
