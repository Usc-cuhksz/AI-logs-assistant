# launcher.py
import os
import sys
import threading
import time
import webbrowser
import traceback
from pathlib import Path

import uvicorn
from app_paths import APP_ROOT, chdir_app_root


# ✅ 永远切到“项目根目录”（你的原始 storage/state/derived 都在这里）
chdir_app_root()


def find_web_dir(basedir: Path) -> Path:
    """
    优先用项目根目录的 web（等同你以前 python 运行 launcher.py 的行为）
    如果项目根没有，再兜底找打包后的 _internal/web
    """
    candidates = [
        basedir / "web",
        Path(sys.executable).resolve().parent / "_internal" / "web" if getattr(sys, "frozen", False) else None,
        getattr(sys, "_MEIPASS", None),
    ]

    expanded = []
    for c in candidates:
        if c is None:
            continue
        if isinstance(c, Path):
            expanded.append(c)
        else:
            expanded.append(Path(c) / "web")

    for d in expanded:
        if (d / "index.html").exists():
            return d

    return basedir / "web"


def msgbox(title: str, text: str):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, 0)
    except Exception:
        print(f"[{title}] {text}")


def start_api_safe(basedir: Path):
    """
    后台启动 FastAPI；失败写 run.log 并弹窗
    """
    log_path = basedir / "run.log"
    try:
        from server.api import app

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_config=None,
        )
    except Exception:
        err = traceback.format_exc()
        log_path.write_text(err, encoding="utf-8")
        msgbox("DemoApp Error", f"后端启动失败，错误已写入：\n{log_path}")


if __name__ == "__main__":
    BASE_DIR = APP_ROOT  # ✅ 项目根目录（不是 dist）

    # ✅ 稳定 import / 相对路径
    os.chdir(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    WEB_DIR = find_web_dir(BASE_DIR)
    index_file = WEB_DIR / "index.html"

    if not index_file.exists():
        msgbox(
            "DemoApp Error",
            "找不到前端页面 index.html。\n"
            f"尝试路径：\n- {BASE_DIR / 'web'}\n- {Path(sys.executable).resolve().parent / '_internal' / 'web'}\n"
            f"当前 BASE_DIR：{BASE_DIR}"
        )
        sys.exit(1)

    # 1) 启动后端
    t = threading.Thread(target=start_api_safe, args=(BASE_DIR,), daemon=True)
    t.start()

    # 2) 等一下
    time.sleep(1.0)

    # 3) 打开页面（保持你原来的 file:// 架构）
    webbrowser.open(index_file.resolve().as_uri())

    # 4) 阻塞主线程
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
