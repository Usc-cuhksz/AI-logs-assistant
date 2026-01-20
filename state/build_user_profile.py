from pathlib import Path
import sys
from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT
sys.path.append(str(APP_ROOT))

from agent.llm import LLMClient
from agent.prompt import prompt_userprofile
from schema.response import log_data_xml
from datetime import datetime
import json
from datetime import date

llm = LLMClient()

def read_all_logs(log_base_dir: Path) -> str:
    """
    读取 storage 下所有 .txt 日志内容，拼成一个大文本
    """
    texts = []

    for folder in ["tasks", "feedback", "events", "goals"]:
        folder_path = log_base_dir / folder
        if not folder_path.exists():
            continue

        for p in sorted(folder_path.glob("*.txt")):
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    texts.append(f"{content}")
            except Exception:
                continue

    return "\n\n".join(texts)
def build_user_profile():
    """
    一天一次调用：
    - 读取全部日志 txt
    - 生成用户画像
    - 覆写 state/user_profile.txt
    """

    # ✅ 确保 state 目录存在（更稳）
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE = STATE_DIR / "user_profile.txt"
    META_FILE = STATE_DIR / "user_profile_meta.json"

    if not should_update_today(META_FILE):
        return

    # ✅ 直接读 exe 同级的 storage
    all_logs_text = read_all_logs(STORAGE_DIR)

    if not all_logs_text:
        OUTPUT_FILE.write_text("当前暂无足够日志数据生成用户画像。", encoding="utf-8")
        write_today_meta(META_FILE)
        return

    profile_text = llm.generate(prompt_userprofile + log_data_xml(all_logs_text))
    OUTPUT_FILE.write_text(profile_text, encoding="utf-8")
    write_today_meta(META_FILE)

def should_update_today(meta_file: Path) -> bool:
    if not meta_file.exists():
        return True
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        last = date.fromisoformat(meta.get("last_updated", ""))
        return last != date.today()
    except Exception:
        return True

def write_today_meta(meta_file: Path):
    meta_file.write_text(
        json.dumps(
            {"last_updated": date.today().isoformat()},
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )