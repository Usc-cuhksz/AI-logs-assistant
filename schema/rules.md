/*
# 📐 项目《路径锚定规则》（内部规范）

下面这部分，你可以原封不动存成一份文档，  
这是你这个项目以后绝对不踩坑的规则。

---

## 📄 AI 日志系统 · 路径锚定内部规范

### 🎯 目标

- 不依赖当前工作目录（`cwd`）  
- 不依赖启动方式（notebook / FastAPI / exe）  
- 所有文件只写到**唯一确定的位置**

---

## 一、唯一合法的路径锚点

项目中任何涉及文件系统的代码，**必须以“文件自身”为锚点**。

✅ **唯一允许的写法**
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

**含义：**

- `__file__`：当前模块文件  
- `.parent`：模块所在目录  
- `.parent.parent`：项目根目录  

🚫 **禁止使用：**

- `Path(".")`
- `Path("./storage")`
- `os.getcwd()`
- 相对路径 `"../"`

---

## 二、项目级标准目录变量（统一命名）

在任何模块中，如需访问核心目录，**必须按下列方式定义**：

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"
STATE_DIR   = BASE_DIR / "state"
DERIVED_DIR = BASE_DIR / "derived"

> 这三个名字是项目保留语义，**不要发明新叫法**。

---

## 三、禁止跨模块“猜路径”

❌ **错误示例**
Path("./state/file_index.json")
Path("../storage/events")

✅ **正确示例**
STATE_DIR / "file_index.json"
STORAGE_DIR / "events" / filename

---

## 四、写文件时的强制规则

1️⃣ **任何写文件前，必须保证父目录存在**
path.parent.mkdir(parents=True, exist_ok=True)

2️⃣ **所有“相对路径”必须是逻辑相对，不是文件系统相对**

例如：
relative_path = "events/去医院.txt"
full_path = STORAGE_DIR / relative_path

🚫 **不允许直接** `open(relative_path)`

---

## 五、模块角色与路径权限

| 模块          | 可以访问                | 不应该访问       |
|---------------|------------------------|------------------|
| `orchestrator`| `storage` / `state` / `derived` | `web`            |
| `state`       | `storage` / `state`    | `web`            |
| `derived`     | `storage` / `derived`  | `state`          |
| `server`      | `orchestrator` / `derived` | `storage`（直接写） |
| `web`         | ❌ 文件系统             | 一切后端路径      |

---

## 六、Notebook 的特殊规则

> **Notebook 永远不是系统的一部分**

✅ **Notebook 允许：**
sys.path.insert(0, PROJECT_ROOT)

❌ **Notebook 不允许：**

- 定义路径规则  
- 决定文件写到哪里  
- 替代模块逻辑
*/