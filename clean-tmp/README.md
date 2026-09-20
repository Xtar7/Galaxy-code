# 系统软件清理工具 v1.0

一款功能强大的系统软件及孤儿数据清理工具，支持图形界面和命令行两种操作模式。

## 功能特性

- **多维度软件扫描**
  - Windows 注册表扫描（系统、家庭用户）
  - 文件系统扫描（Program Files、Program Files (x86)）
  - 包管理器扫描（Winget、Scoop、Chocolatey）
  - 支持扫描 C 盘及自定义路径（如 D:\Programs）

- **应用数据扫描**
  - LOCALAPPDATA（本地应用数据）
  - APPDATA（漫游应用数据）
  - PROGRAMDATA（程序数据）
  - 支持自定义数据路径（如 D:\AppData）

- **智能对比分析**
  - 自动匹配已安装软件与残留数据
  - 字符串相似度算法，模糊匹配
  - 按大小排序，优先处理大文件夹

- **安全清理**
  - 支持回收站删除（可恢复）
  - 支持直接删除（需管理员权限）
  - 演习模式（不实际删除，只分析）
  - 批量选择删除

- **权限管理**
  - 自动请求管理员权限
  - 支持 icacls 强制修改权限后删除
  - PowerShell/CMD 快速启动入口

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.8+
- **权限**: 部分功能需要管理员权限

## 安装说明

### 1. 安装 Python 和 uv

从 [python.org](https://www.python.org/downloads/) 下载并安装 Python 3.8+（安装时勾选 "Add Python to PATH"）。

然后安装 [uv](https://github.com/astral-sh/uv)（推荐方式）：
```bash
# 用 uv 自带的安装脚本
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 创建虚拟环境

在项目根目录运行：
```bash
uv venv
```

### 3. 安装可选依赖（增强功能）

```bash
.venv\Scripts\python -m pip install psutil send2trash pywin32
```

本项目核心功能仅使用 Python 标准库，可选依赖可以不装。

## 使用方法

### 方式一：图形界面（推荐）

双击运行 `run_cleaner.bat` 或 `run_cleaner.ps1`（需管理员权限）。

或在命令行中：
```bash
python main.py
```

### 方式二：命令行

```bash
# 基本扫描
python main.py --cli --scan

# 扫描并自动清理所有孤儿数据
python main.py --cli --scan --clean --auto

# 指定扫描路径
python main.py --cli --scan --custom-install D:\Programs --custom-appdata D:\AppData

# 演习模式（不实际删除）
python main.py --cli --scan --clean --dry-run

# 导出报告
python main.py --cli --scan --export report.json

# 从报告导入并清理
python main.py --cli --import report.json --clean
```

## 界面说明

### 图形界面

界面分为两个主要区域：

- **左侧面板**：显示所有已安装软件列表（名称、版本、发布者、大小、来源）
- **右侧面板**：包含三个标签页
  - **孤儿数据 (待清理)**：列出所有未匹配到已安装软件的残留数据，点击行可切换选择（☑/☐）
  - **所有应用数据**：显示扫描到的所有应用数据文件夹，标注是否为孤儿
  - **扫描日志**：显示详细的扫描过程日志

工具栏提供：
- 扫描/清理/刷新按钮
- 自定义路径输入框
- 演习模式/回收站/管理员权限选项

### 命令行

扫描结果会显示：
- 已安装软件数量
- 应用数据文件夹数量
- 孤儿数据数量及总大小
- 详细的文件列表（索引、名称、大小、文件数、修改时间、匹配软件）

## 权限说明

| 操作 | 所需权限 | 说明 |
|------|---------|------|
| 扫描注册表 | 普通用户 | HKLM 可能需要管理员 |
| 扫描 Program Files | 普通用户 | 大部分可访问 |
| 扫描 AppData | 普通用户 | 用户自有数据 |
| 删除受保护文件 | 管理员 | 使用 `--admin` 参数 |
| icacls 强制权限 | 管理员 | 自动在清理时执行 |

## 架构设计

```
main.py                    - 启动入口（GUI/CLI 选择）
app_cleaner.py             - 核心逻辑模块
  ├── SoftwareScanner      - 软件扫描器（注册表/文件系统/包管理器）
  ├── AppDataScanner       - 应用数据扫描器
  ├── OrphanAnalyzer       - 孤儿数据分析器
  ├── Cleaner              - 清理执行器
  └── AppCleaner           - 主控制器
app_cleaner_gui.py         - 图形界面
run_cleaner.bat            - Windows 批处理启动
run_cleaner.ps1            - PowerShell 启动
```

## 注意事项

1. **演习模式**：首次使用建议使用 `--dry-run` 或勾选"演习模式"，确认结果后再实际删除
2. **回收站**：默认删除到回收站（可恢复），取消勾选"回收站"将永久删除
3. **管理员权限**：清理受保护目录时需要管理员权限，使用 `--admin` 参数或右键"以管理员身份运行"
4. **系统组件**：自动忽略 Microsoft、Windows、驱动等系统组件，避免误删

## 常见问题

**Q: 扫描速度慢？**
A: 首次扫描需要遍历大量目录，属正常现象。后续扫描会快很多。

**Q: 删除失败？**
A: 确保以管理员权限运行。工具会自动尝试修改权限（icacls）后重试。

**Q: 如何选择要删除的项目？**
A: 在"孤儿数据"标签页中，点击行可以切换选择状态（☑/☐），选中的项目才会被清理。

**Q: 误删了怎么办？**
A: 默认删除到回收站，可以从回收站恢复。

## 版本历史

- v1.0 (2026-09-20): 初始版本，支持扫描、对比、清理基本功能
