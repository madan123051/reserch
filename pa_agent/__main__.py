from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config, write_default_config
from .llm import LLMClient
from .memory import MemoryStore
from .tools import SafeTools
from .workflows import Workflows


def build_runtime(config_path: str | None = None) -> tuple[MemoryStore, SafeTools, Workflows]:
    cfg = load_config(Path(config_path) if config_path else None)
    memory = MemoryStore(cfg.memory_dir)
    memory.init()
    tools = SafeTools(cfg)
    llm = LLMClient(cfg)
    return memory, tools, Workflows(memory, llm, tools)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="personal-agent")
    parser.add_argument("--config", help="Path to agent.config.json")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init")
    ask = sub.add_parser("ask")
    ask.add_argument("prompt", nargs="+")

    research = sub.add_parser("research")
    research.add_argument("topic", nargs="+")

    review = sub.add_parser("review")
    review.add_argument("path", nargs="?", default=".")

    deploy = sub.add_parser("deploy-check")
    deploy.add_argument("path", nargs="?", default=".")

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_cmd")
    task_add = task_sub.add_parser("add")
    task_add.add_argument("text", nargs="+")
    task_add.add_argument("--project")
    task_sub.add_parser("list")
    task_done = task_sub.add_parser("done")
    task_done.add_argument("id", type=int)

    note = sub.add_parser("note")
    note_sub = note.add_subparsers(dest="note_cmd")
    note_add = note_sub.add_parser("add")
    note_add.add_argument("text", nargs="+")
    note_search = note_sub.add_parser("search")
    note_search.add_argument("query", nargs="+")

    shell = sub.add_parser("shell")
    shell.add_argument("command", nargs="+")

    read = sub.add_parser("read")
    read.add_argument("path")

    write = sub.add_parser("write")
    write.add_argument("path")
    write.add_argument("--content", required=True)
    write.add_argument("--overwrite", action="store_true")

    search = sub.add_parser("search")
    search.add_argument("query", nargs="+")

    web = sub.add_parser("web")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)

    sub.add_parser("chat")

    args = parser.parse_args(argv)
    if args.cmd == "init":
        config_path = Path(args.config or "agent.config.json")
        if not config_path.exists():
            write_default_config(config_path)
        memory, _, _ = build_runtime(str(config_path))
        print(f"Ready: {config_path.resolve()}")
        print(f"Memory: {memory.root.resolve()}")
        return 0

    memory, tools, workflows = build_runtime(args.config)

    if args.cmd == "ask":
        print(workflows.general_answer(" ".join(args.prompt)))
    elif args.cmd == "research":
        print(workflows.research(" ".join(args.topic)))
    elif args.cmd == "review":
        print(workflows.code_review(args.path))
    elif args.cmd == "deploy-check":
        print(workflows.deploy_check(args.path))
    elif args.cmd == "task":
        handle_task(args, memory)
    elif args.cmd == "note":
        handle_note(args, memory)
    elif args.cmd == "shell":
        result = tools.run_shell(" ".join(args.command))
        print(result.output)
        return 0 if result.ok else 2
    elif args.cmd == "read":
        print(tools.read_file(args.path).output)
    elif args.cmd == "write":
        result = tools.write_file(args.path, args.content, args.overwrite)
        print(result.output)
        return 0 if result.ok else 2
    elif args.cmd == "search":
        print(tools.search_files(" ".join(args.query)).output)
    elif args.cmd == "web":
        from .web import main as web_main

        web_args = ["--host", args.host, "--port", str(args.port)]
        if args.config:
            web_args.extend(["--config", args.config])
        return web_main(web_args)
    elif args.cmd == "chat" or args.cmd is None:
        chat_loop(memory, tools, workflows)
    else:
        parser.print_help()
    return 0


def handle_task(args: argparse.Namespace, memory: MemoryStore) -> None:
    if args.task_cmd == "add":
        task = memory.add_task(" ".join(args.text), args.project)
        print(f"Added task #{task['id']}")
    elif args.task_cmd == "done":
        print("Done" if memory.complete_task(args.id) else "Task not found")
    else:
        for task in memory.load_tasks():
            mark = "x" if task.get("status") == "done" else " "
            project = f" [{task.get('project')}]" if task.get("project") else ""
            print(f"[{mark}] #{task['id']}{project} {task['text']}")


def handle_note(args: argparse.Namespace, memory: MemoryStore) -> None:
    if args.note_cmd == "add":
        memory.add_note(" ".join(args.text))
        print("Note saved")
    elif args.note_cmd == "search":
        hits = memory.search_notes(" ".join(args.query))
        print("\n".join(hits) if hits else "No matches")
    else:
        print(memory.notes_path.read_text(encoding="utf-8"))


def chat_loop(memory: MemoryStore, tools: SafeTools, workflows: Workflows) -> None:
    print("Personal Agent ready. Type /help, /exit, or ask normally.")
    while True:
        try:
            text = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not text:
            continue
        if text in {"/exit", "exit", "quit"}:
            return
        if text == "/help":
            print(HELP)
        elif text.startswith("/task "):
            task = memory.add_task(text[6:].strip())
            print(f"Added task #{task['id']}")
        elif text == "/tasks":
            handle_task(argparse.Namespace(task_cmd="list"), memory)
        elif text.startswith("/note "):
            memory.add_note(text[6:].strip())
            print("Note saved")
        elif text.startswith("/shell "):
            print(tools.run_shell(text[7:].strip()).output)
        elif text.startswith("/research "):
            print(workflows.research(text[10:].strip()))
        elif text.startswith("/review"):
            print(workflows.code_review(text.replace("/review", "", 1).strip() or "."))
        elif text.startswith("/deploy"):
            print(workflows.deploy_check(text.replace("/deploy", "", 1).strip() or "."))
        else:
            print(workflows.general_answer(text))


HELP = """Commands:
/task <text>          add a task
/tasks                list tasks
/note <text>          save a note
/shell <command>      run an allowlisted shell command
/research <topic>     create a research plan and save it
/review [path]        review git status/diff
/deploy [path]        deployment readiness checklist
/exit                 quit
"""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
