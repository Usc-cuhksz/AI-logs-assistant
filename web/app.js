const API = "http://127.0.0.1:8000/api";

let useHistory = false;
let logsVisible = false;
let activeLogs = [];
let loadingNode = null;

const logNames = {
  tasks: "TASKS",
  feedback: "FEEDBACK",
  events: "EVENTS",
  goals: "GOALS"
};

/* ---------- 对话 ---------- */

function addMessage(role, text) {
  const box = document.getElementById("chatBox");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function showLoading() {
  const box = document.getElementById("chatBox");
  const div = document.createElement("div");
  div.className = "msg loading";
  div.innerHTML = `<div class="spinner"></div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  loadingNode = div;
}

function hideLoading() {
  if (loadingNode) {
    loadingNode.remove();
    loadingNode = null;
  }
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  let text = input.value.trim();
  if (!text) return;

  input.value = "";
  addMessage("user", text);

  if (useHistory) {
    text = "-" + text;
  }

  showLoading();

  try {
    const res = await fetch(API + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    const data = await res.json();
    hideLoading();
    addMessage("ai", data.reply);

  } catch (e) {
    hideLoading();
    addMessage("ai", "（发生错误，无法获取回复）");
  }
}

/* ---------- 日志 ---------- */

function ensureLogsOpen() {
  logsVisible = true;
  document.getElementById("leftPane").classList.remove("hidden");
}

function closeLogs() {
  logsVisible = false;
  activeLogs = [];
  const pane = document.getElementById("leftPane");
  pane.innerHTML = "";
  pane.classList.add("hidden");
  document.querySelectorAll(".logBtn")
    .forEach(b => b.classList.remove("active"));
}

async function toggleLog(type) {
  ensureLogsOpen();

  const idx = activeLogs.indexOf(type);
  const btn = document.querySelector(`.logBtn[data-log="${type}"]`);

  if (idx >= 0) {
    activeLogs.splice(idx, 1);
    btn.classList.remove("active");
  } else {
    activeLogs.push(type);
    btn.classList.add("active");
  }

  if (activeLogs.length === 0) {
    closeLogs();
    return;
  }

  await renderLogs();
}

async function renderLogs() {
  const pane = document.getElementById("leftPane");
  pane.innerHTML = "";

  const height = 100 / activeLogs.length;

  for (const type of activeLogs) {
    const block = document.createElement("div");
    block.className = "logBlock";
    block.style.height = height + "%";

    const header = document.createElement("div");
    header.className = "logHeader";
    header.textContent = logNames[type];
    header.onclick = () => toggleLog(type);

    const content = document.createElement("div");
    content.className = "logContent";
    content.textContent = "Loading...";

    block.append(header, content);
    pane.appendChild(block);

    const res = await fetch(API + "/derived/" + type);
    const data = await res.json();
    content.textContent = data.content || "";
  }
}

/* ---------- 工具栏 ---------- */

document.getElementById("toggleLogs").onclick = () => {
  logsVisible ? closeLogs() : ensureLogsOpen();
};

document.querySelectorAll(".logBtn").forEach(btn => {
  btn.onclick = () => toggleLog(btn.dataset.log);
});

document.getElementById("toggleHistory").onclick = (e) => {
  useHistory = !useHistory;
  e.target.classList.toggle("active", useHistory);
  e.target.textContent = useHistory ? "● Use History" : "◯ Use History";
};

/* ---------- 输入 ---------- */

document.getElementById("sendBtn").onclick = sendChat;

document.getElementById("chatInput")
  .addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  });
