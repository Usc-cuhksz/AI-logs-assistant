from pathlib import Path
from datetime import datetime
import re
from app_paths import STORAGE_DIR, STATE_DIR, DERIVED_DIR, WEB_DIR, APP_ROOT

# ========= 路径定义 =========


LOG_TYPES = ["tasks", "feedback", "events", "goals"]

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


# ========= 工具函数 =========

def extract_date_from_filename(filename: str) -> datetime | None:
    """
    从文件名中提取 YYYY-MM-DD
    例：
      2026-01-03.txt           -> 2026-01-03
      香港行程2025-12-31.txt   -> 2025-12-31
    """
    match = DATE_PATTERN.search(filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(), "%Y-%m-%d")
    except ValueError:
        return None


def read_and_sort_logs(log_type: str) -> list[dict]:
    """
    读取某一类日志，并按日期倒序排序
    """
    folder = STORAGE_DIR / log_type
    if not folder.exists():
        return []

    items = []

    for f in folder.glob("*.txt"):
        date = extract_date_from_filename(f.name)
        try:
            content = f.read_text(encoding="utf-8").strip()
        except Exception:
            continue

        if not content:
            continue

        items.append({
            "filename": f.name,
            "date": date,
            "content": content
        })

    # 日期近的在前，没日期的放最后
    items.sort(
        key=lambda x: x["date"] if x["date"] else datetime.min,
        reverse=True
    )

    return items


def format_logs_for_display(items: list[dict]) -> str:
    """
    将日志整理成“直接可展示”的文本
    """
    blocks = []

    for item in items:
        date_str = (
            item["date"].strftime("%Y-%m-%d")
            if item["date"]
            else "NO_DATE"
        )

        block = (
            f"===== {date_str} | {item['filename']} =====\n"
            f"{item['content']}\n"
        )
        blocks.append(block)

    return "\n".join(blocks)


def write_derived_file(log_type: str, content: str):
    """
    写入 derived/{log_type}.txt
    """
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DERIVED_DIR / f"{log_type}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


# ========= 主入口 =========

def build_derived_logs():
    """
    构建四类日志的派生汇总文件
    """
    for log_type in LOG_TYPES:
        items = read_and_sort_logs(log_type)
        formatted = format_logs_for_display(items)
        write_derived_file(log_type, formatted)


# ========= 允许独立运行 =========

if __name__ == "__main__":
    build_derived_logs()
    # print("✓ derived logs rebuilt")
