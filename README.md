# Personal AI Agent

Private learning agent and web dashboard for research, coding, debugging, and
deployment planning.

This is a clean personal-use scaffold. It does not copy the reverse-engineered
Claude Code project. It gives you the same core learning ideas in a small codebase:
memory, tasks, safe tools, research workflows, code review, and deployment checks.

## Quick Start Webapp

```powershell
cd "C:\Users\madan\Documents\Codex\2026-06-19\files-mentioned-by-the-user-cl\outputs\personal-ai-agent"
python -m pa_agent init
python -m pa_agent web
```

Open:

```text
http://127.0.0.1:8765
```

## Quick Start CLI

```powershell
cd "C:\Users\madan\Documents\Codex\2026-06-19\files-mentioned-by-the-user-cl\outputs\personal-ai-agent"
python -m pa_agent init
python -m pa_agent chat
```

No dependencies are required for local/offline mode.

## Enable AI Answers

Set an API key and model name before running:

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:AI_MODEL="your_model_name"
python -m pa_agent ask "Plan my coding work for today"
```

The agent uses the OpenAI-compatible `/responses` endpoint by default. You can
change `openai_base_url` in `agent.config.json` for another compatible provider.

## Useful Commands

```powershell
python -m pa_agent task add "Build login page" --project my-app
python -m pa_agent task list
python -m pa_agent task done 1

python -m pa_agent note add "React project uses Vite and Tailwind"
python -m pa_agent note search "Vite"

python -m pa_agent research "best auth setup for Next.js app"
python -m pa_agent review .
python -m pa_agent deploy-check .

python -m pa_agent shell "git status"
python -m pa_agent search "TODO"
python -m pa_agent read "README.md"
python -m pa_agent web --port 8765
```

## Chat Commands

Inside `python -m pa_agent chat`:

```text
/task Fix failing deployment
/tasks
/note Use Vercel for frontend deploy
/research OAuth options for SaaS
/review .
/deploy .
/shell git status
/exit
```

Anything else is sent to the model if `OPENAI_API_KEY` and `AI_MODEL` are set.
Without a model, the agent returns an offline practical plan.

## Safety Model

Shell commands are allowlisted in `agent.config.json`.

Blocked examples:

- recursive force deletes
- shutdown/restart commands
- disk formatting patterns

This is intentionally conservative. Add commands only when you trust them.

## Put On GitHub

Personal runtime files are ignored by `.gitignore`:

- `agent.config.json`
- `.env`
- `memory/*.md`
- `memory/*.json`
- `memory/research/*.md`

Create a repository:

```powershell
git init
git add .
git commit -m "Initial personal AI agent webapp"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/personal-ai-agent.git
git push -u origin main
```

## How To Extend

- Edit the web UI in `pa_agent/static/index.html`
- Edit web styles in `pa_agent/static/styles.css`
- Edit browser behavior in `pa_agent/static/app.js`
- Add API routes in `pa_agent/web.py`
- Add new memory behavior in `pa_agent/memory.py`
- Add safe file/shell/web tools in `pa_agent/tools.py`
- Add higher-level workflows in `pa_agent/workflows.py`
- Add CLI commands in `pa_agent/__main__.py`

Good next features:

- PDF summarizer
- browser/search connector
- GitHub issue/PR helper
- deploy provider helper for Vercel/Netlify/Docker
- scheduled daily planning command

## Project Layout

```text
personal-ai-agent/
  pa_agent/
    __main__.py      CLI and chat loop
    config.py        config loading and safety defaults
    llm.py           OpenAI-compatible Responses API adapter
    memory.py        tasks, notes, profile, research files
    tools.py         safe file/search/shell tools
    web.py           local web API server
    workflows.py     research, review, deploy workflows
    static/          dashboard HTML/CSS/JS
  memory/
    profile.md
    notes.md
    tasks.json
    research/
  tests/
```
