from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .llm import LLMClient
from .memory import MemoryStore
from .tools import SafeTools


@dataclass
class Workflows:
    memory: MemoryStore
    llm: LLMClient
    tools: SafeTools

    def research(self, topic: str) -> str:
        prompt = f"""Research this topic for a solo developer:

{topic}

Return:
- Key questions to answer
- Search terms
- What sources/files to collect
- A short learning path
- A practical next action
"""
        answer = self.llm.complete(prompt, self.memory.context_summary())
        path = self.memory.save_research(topic, f"# Research: {topic}\n\n{answer}\n")
        return f"{answer}\n\nSaved: {path}"

    def code_review(self, path: str = ".") -> str:
        status = self.tools.run_shell("git status --short").output
        diff = self.tools.run_shell("git diff --stat").output
        prompt = f"""Review this project/change for a solo developer.

Focus on bugs, risky changes, missing tests, and simple next steps.

Target path: {path}

git status:
{status}

git diff --stat:
{diff}
"""
        return self.llm.complete(prompt, self.memory.context_summary())

    def deploy_check(self, path: str = ".") -> str:
        root = (self.tools.config.workspace / path).resolve()
        signals = []
        for name in [
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Dockerfile",
            "vercel.json",
            "netlify.toml",
            ".env",
            ".env.example",
        ]:
            p = root / name
            if p.exists():
                signals.append(f"- {name}")
        prompt = f"""Create a deployment readiness checklist.

Project path: {root}
Detected files:
{chr(10).join(signals) if signals else "- no common deploy files detected"}

Cover:
- required environment variables
- build/test commands to run
- likely deployment target
- rollback plan
- things not to commit
"""
        return self.llm.complete(prompt, self.memory.context_summary())

    def general_answer(self, text: str) -> str:
        return self.llm.complete(text, self.memory.context_summary())
