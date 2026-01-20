from pathlib import Path
from typing import Dict, List
from datetime import datetime
import json
from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT

def collect_log_filenames(base_dir: str) -> Dict[str, List[str]]:
    """
    扫描日志目录，只返回文件名（不包含路径）
    返回结构：
    {
        "tasks": [...],
        "feedback": [...],
        "events": [...],
        "goals": [...]
    }
    """
    base = Path(base_dir)
    folders = ["tasks", "feedback", "events", "goals"]

    result = {}

    for folder in folders:
        folder_path = base / folder

        if not folder_path.exists() or not folder_path.is_dir():
            result[folder] = []
            continue

        filenames = sorted(
            p.name
            for p in folder_path.iterdir()
            if p.is_file() and p.suffix == ".txt"
        )

        result[folder] = filenames

    return result

def build_file_index():
    """
    编排层直接调用的函数：
    - 扫描 ../storage 下的日志文件
    - 生成文件索引
    - 覆写写入 state/file_index.json
    """

    # 1️⃣ 固定路径（你要求的）
    # ✅ 正确：锚定到项目根目录
    # BASE_DIR = Path(__file__).resolve().parent.parent
    # LOG_BASE_DIR = BASE_DIR / "storage"
    # STATE_DIR = BASE_DIR / "state"
    OUTPUT_FILE = STATE_DIR / "file_index.json"


    # 2️⃣ 确保 state 目录存在
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # 3️⃣ 调用你已有的扫描逻辑
    # index = collect_log_filenames(str(LOG_BASE_DIR))
    index = collect_log_filenames(str(STORAGE_DIR))

    # # 4️⃣ 可选：加一点元信息（非常推荐）
    # index["_meta"] = {
    #     "generated_at": datetime.now().isoformat(),
    #     "log_base_dir": str(LOG_BASE_DIR)
    # }

    # 5️⃣ 覆写写入 JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # 6️⃣ （可选）返回 index，方便调试
    return index