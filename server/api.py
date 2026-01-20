from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# ⭐ 引入你的 Orchestrator
from orchestrator.run import Orchestrator

from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT

# ---------- FastAPI 初始化 ----------

app = FastAPI()

# 允许本地前端直接访问（开发阶段）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 全局 Orchestrator（一个会话） ----------

orchestrator = Orchestrator()

# ---------- 数据模型 ----------

class ChatRequest(BaseModel):
    text: str

# ---------- API：聊天 ----------

@app.post("/api/chat")
def chat(req: ChatRequest):
    result = orchestrator.step(req.text)
    return {
        "reply": result["reply"],
        "state": result.get("state"),
        "saved": result.get("saved", False)
    }

# ---------- API：查看派生日志 ----------

@app.get("/api/derived/{log_type}")
def get_derived(log_type: str):
    file = DERIVED_DIR / f"{log_type}.txt"
    if not file.exists():
        return {"content": ""}
    return {"content": file.read_text(encoding="utf-8")}
