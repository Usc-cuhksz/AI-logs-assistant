# app_paths.py
from pathlib import Path
import os
import sys


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "executable")


def _looks_like_project_root(p: Path) -> bool:
    """
    你所谓“原来的数据结构所在的项目根目录”应当满足：
    - 有 storage/
    - 并且有 server/（源码目录一定有；dist/DemoApp 一般没有）
    这样就能避免误把 dist/DemoApp 当作根目录。
    """
    return (p / "storage").is_dir() and (p / "server").is_dir()


def _find_project_root(start: Path, max_up: int = 12) -> Path:
    """
    从 exe 所在目录开始往上找，直到找到真正的项目根目录（包含 storage + server）。
    找不到就直接报错（宁愿报错，也绝不偷偷在 dist 里新建一套空数据）。
    """
    cur = start.resolve()
    for _ in range(max_up + 1):
        if _looks_like_project_root(cur):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    raise RuntimeError(
        "找不到你的项目根目录（需要同时存在 storage/ 和 server/）。\n"
        f"起点：{start}\n"
        "解决方式：\n"
        "1) 确保 exe 仍放在你的项目目录内部（通常是 项目根/dist/DemoApp/DemoApp.exe），或\n"
        "2) 设置环境变量 AI_LOG_ROOT=你的项目根目录（包含 storage 和 server 的那个目录）。"
    )


def get_app_root() -> Path:
    """
    目标：无论 exe 还是 py，永远使用“原来的项目根目录”作为根目录。
    """
    env_root = os.environ.get("AI_LOG_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve()
        if not _looks_like_project_root(p):
            raise RuntimeError(f"AI_LOG_ROOT 指向的目录不是项目根（缺 storage/ 或 server/）：{p}")
        return p

    if _is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        return _find_project_root(exe_dir)

    # 开发态：app_paths.py 放在项目根目录（你现在就是这样）
    return Path(__file__).resolve().parent


APP_ROOT = get_app_root()

STORAGE_DIR = APP_ROOT / "storage"
STATE_DIR = APP_ROOT / "state"
DERIVED_DIR = APP_ROOT / "derived"
WEB_DIR = APP_ROOT / "web"


def chdir_app_root() -> None:
    os.chdir(str(APP_ROOT))
