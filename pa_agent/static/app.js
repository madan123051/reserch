const views = {
  chat: ["Chat", "Ask for research, code, deployment, or learning help."],
  research: ["Research", "Create focused research plans and save them to memory."],
  code: ["Code", "Review local git status and change summaries."],
  deploy: ["Deploy", "Check project readiness before publishing."],
  tasks: ["Tasks", "Track work across research, coding, and deployment."],
  notes: ["Notes", "Save and search private learning notes."],
  tools: ["Tools", "Run allowlisted shell commands and file searches."]
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

function setBusy(target, busyText = "Working...") {
  target.textContent = busyText;
}

function appendMessage(role, text) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = text;
  $("chatLog").appendChild(node);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
}

function activate(view) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === view);
  });
  $("viewTitle").textContent = views[view][0];
  $("viewSub").textContent = views[view][1];
  if (view === "tasks") loadTasks();
  if (view === "notes") loadNotes();
}

async function refreshStatus() {
  const status = await api("/api/status");
  $("modelStatus").textContent = status.model_connected
    ? `Model: ${status.model}`
    : "Offline mode";
  $("workspaceText").textContent = status.workspace;
}

async function loadTasks() {
  const data = await api("/api/tasks");
  const list = $("taskList");
  list.innerHTML = "";
  if (!data.tasks.length) {
    list.innerHTML = '<div class="message">No tasks yet.</div>';
    return;
  }
  data.tasks.forEach((task) => {
    const row = document.createElement("div");
    row.className = `task-row ${task.status === "done" ? "done" : ""}`;
    const mark = document.createElement("strong");
    mark.textContent = task.status === "done" ? "Done" : "Open";
    const body = document.createElement("div");
    body.innerHTML = `<div>${escapeHtml(task.text)}</div><small>#${task.id}${task.project ? ` · ${escapeHtml(task.project)}` : ""}</small>`;
    const button = document.createElement("button");
    button.className = "secondary";
    button.textContent = "Done";
    button.disabled = task.status === "done";
    button.addEventListener("click", async () => {
      await api("/api/tasks/done", {
        method: "POST",
        body: JSON.stringify({ id: task.id })
      });
      loadTasks();
    });
    row.append(mark, body, button);
    list.appendChild(row);
  });
}

async function loadNotes() {
  const data = await api("/api/notes");
  $("notesOut").textContent = data.notes;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => activate(tab.dataset.view));
});

$("refreshBtn").addEventListener("click", refreshStatus);

$("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("chatInput").value.trim();
  if (!text) return;
  $("chatInput").value = "";
  appendMessage("user", text);
  appendMessage("assistant", "Working...");
  const last = $("chatLog").lastChild;
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text })
    });
    last.textContent = data.output;
  } catch (error) {
    last.textContent = error.message;
    last.classList.add("danger");
  }
});

$("researchBtn").addEventListener("click", async () => {
  setBusy($("researchOut"));
  try {
    const data = await api("/api/research", {
      method: "POST",
      body: JSON.stringify({ topic: $("researchTopic").value })
    });
    $("researchOut").textContent = data.output;
  } catch (error) {
    $("researchOut").textContent = error.message;
  }
});

$("reviewBtn").addEventListener("click", async () => {
  setBusy($("reviewOut"));
  try {
    const data = await api("/api/review", {
      method: "POST",
      body: JSON.stringify({ path: $("reviewPath").value })
    });
    $("reviewOut").textContent = data.output;
  } catch (error) {
    $("reviewOut").textContent = error.message;
  }
});

$("deployBtn").addEventListener("click", async () => {
  setBusy($("deployOut"));
  try {
    const data = await api("/api/deploy", {
      method: "POST",
      body: JSON.stringify({ path: $("deployPath").value })
    });
    $("deployOut").textContent = data.output;
  } catch (error) {
    $("deployOut").textContent = error.message;
  }
});

$("taskForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("taskText").value.trim();
  if (!text) return;
  await api("/api/tasks", {
    method: "POST",
    body: JSON.stringify({ text, project: $("taskProject").value.trim() })
  });
  $("taskText").value = "";
  loadTasks();
  refreshStatus();
});

$("noteAddBtn").addEventListener("click", async () => {
  const text = $("noteInput").value.trim();
  if (!text) return;
  const data = await api("/api/notes", {
    method: "POST",
    body: JSON.stringify({ text })
  });
  $("noteInput").value = "";
  $("notesOut").textContent = data.notes;
});

$("noteSearchBtn").addEventListener("click", async () => {
  const data = await api("/api/notes/search", {
    method: "POST",
    body: JSON.stringify({ query: $("noteQuery").value })
  });
  $("notesOut").textContent = data.hits.length ? data.hits.join("\n") : "No matches";
});

$("shellBtn").addEventListener("click", async () => {
  setBusy($("toolsOut"));
  try {
    const data = await api("/api/shell", {
      method: "POST",
      body: JSON.stringify({ command: $("shellCommand").value })
    });
    $("toolsOut").textContent = data.output || (data.ok ? "Done" : "No output");
  } catch (error) {
    $("toolsOut").textContent = error.message;
  }
});

$("fileSearchBtn").addEventListener("click", async () => {
  setBusy($("toolsOut"));
  try {
    const params = new URLSearchParams({ q: $("fileSearch").value });
    const data = await api(`/api/search?${params.toString()}`);
    $("toolsOut").textContent = data.output;
  } catch (error) {
    $("toolsOut").textContent = error.message;
  }
});

appendMessage("assistant", "Ready. Ask me about research, coding, deployment, or your learning plan.");
refreshStatus().catch((error) => {
  $("modelStatus").textContent = error.message;
});
