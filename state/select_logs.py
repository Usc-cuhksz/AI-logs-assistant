from pathlib import Path
import json
import sys
from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT

# # ===== 路径兜底（确保从 app.py 调用也不炸）=====
# BASE_DIR = Path(__file__).resolve()
# while not (BASE_DIR / "storage").exists():
#     if BASE_DIR.parent == BASE_DIR:
#         raise FileNotFoundError("Cannot locate project root: missing 'storage' directory")
#     BASE_DIR = BASE_DIR.parent
# STORAGE_DIR = BASE_DIR / "storage"

# ===== 你已有的组件 =====
from agent.llm import LLMClient
from agent.prompt import prompt_file_router  # 你的系统提示词
from schema.response import parse_llm_json,file_list_xml,user_xml,user_profile_xml   # 你已有的 JSON parser

llm = LLMClient()


def _load_user_profile(state_dir: Path) -> str:
    profile_file = state_dir / "user_profile.txt"
    if not profile_file.exists():
        return ""
    return profile_file.read_text(encoding="utf-8").strip()


def _load_file_index(state_dir: Path) -> dict:
    index_file = state_dir / "file_index.json"
    if not index_file.exists():
        return {}
    try:
        return json.loads(index_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def select_relevant_logs(user_input: str) -> str:
    """
    Planner 节点（同步）：
    输入：
      - user_input
    读取：
      - state/user_profile.txt
      - state/file_index.json
    输出：
        日志文本字符串
    """

    # ===== 路径锚定（稳健，和 app.py 在同一项目根目录）=====
    # STATE_DIR = Path(__file__).resolve().parent

    user_profile = _load_user_profile(STATE_DIR)
    file_index = _load_file_index(STATE_DIR)

    # ===== 调用 LLM =====
    raw_output = llm.generate(
        prompt_file_router+user_xml(user_input)+file_list_xml(file_index)+user_profile_xml(user_profile)
    )

    # ===== 解析 JSON（你已有工具）=====
    result = parse_llm_json(raw_output)

    # ===== 防御式兜底 =====
    if not isinstance(result, dict):
        return ''

    if result.get("type") != "3-1":
        return ''

    # 确保 paths 结构存在
    paths = result.get("content", [])
    if not isinstance(paths, list):
        paths = []

    log_chunks = []

    for rel_path in paths:
        if not isinstance(rel_path, str):
            continue

        # 防御：只取相对路径，避免 ../
        rel_path = Path(rel_path)

        file_path = STORAGE_DIR / rel_path

        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8").strip()
            if content:
                log_chunks.append(
                    f"【{rel_path.as_posix()}】\n{content}"
                )
        except Exception:
            continue

    log_text = "\n\n".join(log_chunks)
    # ===== 这里结束 =====

    return log_text

