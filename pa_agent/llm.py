from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import AgentConfig


SYSTEM_PROMPT = """You are a private personal AI agent for one user.
Help with research, coding, debugging, deployment planning, and learning.
Be practical, concise, and safety-aware.
When commands or file edits are needed, suggest small verifiable steps.
Never claim you ran a command unless tool output was provided.
"""


@dataclass
class LLMClient:
    config: AgentConfig

    def available(self) -> bool:
        return bool(self.config.api_key and self.config.model)

    def complete(self, prompt: str, context: str = "") -> str:
        if not self.available():
            return self.offline_response(prompt)

        url = self.config.openai_base_url.rstrip("/") + "/responses"
        payload = {
            "model": self.config.model,
            "instructions": SYSTEM_PROMPT + "\n\nUser memory/context:\n" + context,
            "input": prompt,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as res:
                data = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return f"LLM request failed: HTTP {e.code}\n{body}"
        except Exception as e:
            return f"LLM request failed: {e}"

        return extract_text(data) or json.dumps(data, indent=2)[:4000]

    def offline_response(self, prompt: str) -> str:
        return (
            "AI model is not connected yet.\n\n"
            "Set these environment variables to enable model answers:\n"
            "- OPENAI_API_KEY\n"
            "- AI_MODEL\n\n"
            "For now, here is a practical offline plan:\n"
            f"1. Clarify the goal: {prompt.strip()[:180]}\n"
            "2. Gather files, links, logs, or error messages.\n"
            "3. Break the work into research, implementation, verification, and deploy.\n"
            "4. Run the smallest safe command/check first.\n"
            "5. Save useful findings into memory with `note add ...`.\n"
        )


def extract_text(data: dict) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    chunks: list[str] = []
    for item in data.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text") or content.get("output_text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()
