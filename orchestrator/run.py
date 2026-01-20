# orchestrator/run.py
"""
编排层 Orchestrator

职责：
- 接收单条用户输入
- 维护对话状态（S1 / S2）
- 决定是否使用日志
- 调用 LLM
- 保存日志 & 触发派生构建
- 返回结构化结果（不 print）

注意：
- 不负责 UI
- 不负责 HTTP
- 不包含 input() / while True / print()
"""
from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT

from datetime import date
import threading
from pathlib import Path


from agent.llm import LLMClient
from agent.prompt import prompt1, prompt2

from schema.response import (
    parse_llm_json,
    user_xml,
    log_xml,
    context_to_text,
    log_data_xml
)

from state.build_user_profile import build_user_profile
from state.select_logs import select_relevant_logs
from state.build_file_index import build_file_index

from derived.build_derived_logs import build_derived_logs

# =========================
# 内部工具函数
# =========================

def trigger_user_profile_async():
    """
    后台异步触发用户画像更新
    """
    t = threading.Thread(
        target=build_user_profile,
        daemon=True
    )
    t.start()


def get_log(user_input: str) -> str:
    """
    根据用户输入选择相关历史日志
    """
    log_text = select_relevant_logs(user_input)
    if not log_text:
        return ''
    return log_data_xml(log_text)


# =========================
# Orchestrator
# =========================

class Orchestrator:
    """
    一个有状态的编排器实例
    - 每个“会话”对应一个实例
    """

    def __init__(self):
        # LLM
        self.llm = LLMClient()

        # 启动时异步更新用户画像（一次即可）
        trigger_user_profile_async()

        # 状态机
        self.current_state = 'S1'   # S1: 自由聊天 / 判断日志
                                      # S2: 日志确认阶段

        # 对话上下文
        self.context = []           # [{'role': 'user'/'assistant', 'content': str}]
        self.draft_log = None       # 日志草稿（S2 使用）

        # 当前日期
        today = date.today()
        self.cur_date = f'<current_date>{today}</current_date>'

    # =========================
    # 对外唯一入口
    # =========================

    def step(self, user_input: str) -> dict:
        """
        处理一条用户输入，返回结构化结果

        返回示例：
        {
          "reply": "...",
          "state": "S1" / "S2",
          "draft_log": "...",      # 可选
          "saved": True            # 可选
        }
        """

        user_input = user_input.strip()
        if not user_input:
            return {
                "reply": "",
                "state": self.current_state
            }

        # ========== 记录用户输入 ==========
        self.context.append({
            "role": "user",
            "content": user_input
        })

        # ========== 是否启用日志 ==========
        if user_input.startswith('-'):
            log_previous = get_log(user_input)
        else:
            log_previous = ''

        # =====================================================
        # 状态 S1：自由聊天 / 日志意图判断
        # =====================================================
        if self.current_state == 'S1':

            if len(self.context) == 1:
                previous_context = str(self.context[0])
            else:
                previous_context = context_to_text(self.context)

            raw_prompt = (
                log_previous
                + previous_context
                + prompt1
                + self.cur_date
                + user_xml(user_input)
            )

            result = parse_llm_json(self.llm.generate(raw_prompt))

            # ---------- 1-1：识别为日志 ----------
            if result.get("type") == "1-1":
                # 回退上下文（日志草稿不算正常对话）
                self.context.pop()

                self.current_state = "S2"
                self.draft_log = result["content"]

                return {
                    "reply": result["content"],
                    "state": self.current_state,
                    "draft_log": self.draft_log
                }

            # ---------- 1-2：正常聊天 ----------
            elif result.get("type") == "1-2":
                self.context.append({
                    "role": "assistant",
                    "content": result["content"]
                })

                return {
                    "reply": result["content"],
                    "state": self.current_state
                }

            # ---------- 异常 ----------
            else:
                return {
                    "reply": "LLM error",
                    "state": self.current_state
                }

        # =====================================================
        # 状态 S2：日志确认阶段
        # =====================================================
        else:
            raw_prompt = (
                log_previous
                + log_xml(self.draft_log)
                + prompt2
                + user_xml(user_input)
            )

            result = parse_llm_json(self.llm.generate(raw_prompt))

            # ---------- 2-1：确认并保存 ----------
            if result.get("type") == "2-1":
                text = result["content"][1]
                relative_path = result["content"][0]          # e.g. "events/去医院就诊2026-01-05.txt"
                path = STORAGE_DIR / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)

                # 状态复位
                self.context.pop()      # S2 输入不计入上下文
                self.current_state = "S1"
                self.draft_log = None

                # 更新索引与派生文件
                build_file_index()
                build_derived_logs()

                return {
                    "reply": "好的，该日志已保存！",
                    "state": self.current_state,
                    "saved": True
                }

            # ---------- 2-2：修改草稿 ----------
            elif result.get("type") == "2-2":
                self.context.pop()
                self.draft_log = result["content"]

                return {
                    "reply": result["content"],
                    "state": self.current_state,
                    "draft_log": self.draft_log
                }

            # ---------- 2-3：跳出日志，正常聊天 ----------
            elif result.get("type") == "2-3":
                self.context.append({
                    "role": "assistant",
                    "content": result["content"]
                })

                self.current_state = "S1"
                self.draft_log = None

                return {
                    "reply": result["content"],
                    "state": self.current_state
                }

            # ---------- 异常 ----------
            else:
                return {
                    "reply": "LLM error",
                    "state": self.current_state
                }
