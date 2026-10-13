# Galaxy Code — 代码与工具集合

> 个人工具箱 & 代码片段仓库，持续更新中。每个工具独立运行，即开即用。

---

## 目录

| # | 项目 | 简介 | 在线访问 | 类型 |
|---|------|------|----------|------|
| 1 | [DataForge](#1-dataforge) | 浏览器端数据工作台 | [在线使用](https://xtar7.github.io/Galaxy-code/DataForge) | 前端工具 |
| 2 | [Traceability](#2-traceability) | 身份证模拟号生成器（测试数据） | [在线使用](https://xtar7.github.io/Galaxy-code/Traceability) | 前端工具 |
| 3 | [Pentest Command Builder Pro](#3-pentest-command-builder-pro) | 渗透测试命令生成器 / 速查手册 | [在线使用](https://xtar7.github.io/Galaxy-code/PentestCB) | 前端工具 |
| 4 | [EZ 指纹规则生成器](#4-ez-指纹规则生成器) | 一键生成 EZ 指纹规则 JSON | [在线使用](https://xtar7.github.io/Galaxy-code/finger) | 前端工具 |
| 5 | [OpenRouter 免费模型速查](#5-openrouter-免费模型速查) | 自动抓取 OpenRouter 免费模型，支持筛选/搜索/分页 | [本地运行](https://xtar7.github.io/Galaxy-code/or-free-models) | 前后端工具 |
| 6 | [系统软件清理工具](#6-系统软件清理工具) | 扫描并清理 Windows 孤立软件与残留数据 | [本地运行](clean-tmp/) | 系统工具 |
| 7 | [HashDock](#7-hashdock-文件完整性校验) | 文件哈希计算与完整性复核（SHA-256 清单工具） | [在线使用](https://xtar7.github.io/Galaxy-code/HashDock) | 前端工具 |

---

## 1. DataForge

**浏览器端数据工作台** — 纯前端、零依赖（除 XLSX 导出外）、无需后端的数据处理工具。上传 CSV/TSV/JSON，在浏览器中完成筛选、合并、拆分、清洗、字段重组、多表关联等操作。

### 功能特性

| 模块 | 功能 |
|------|------|
| 筛选与合并 | 多文件选择、列选择、多条件筛选、数据预览（1/3/5行）、纵向合并/交集/不合并 |
| 字段映射重组 | 跨表字段挑选、计算列公式（`{单价}*{数量}`）、正则提取特定值 |
| 多表关联 | 左连接/内连接，按关键字段关联多个表 |
| 条件拆分 | 按列值拆分 / 按自定义条件拆分 |
| 数据清洗 | 去空格、删空行/空列、去重、填充空值、统一列名大小写 |
| 预览与导出 | 表格预览、导出 XLSX/CSV/Markdown、一键复制到剪贴板 |

### 使用方式

- **在线使用**：直接访问 [GitHub Pages](https://xtar7.github.io/Galaxy-code/DataForge)
- **本地使用**：下载 `DataForge/index.html`，双击用浏览器打开
- **内网部署**：拷贝到内网服务器或共享目录即可

### 支持的文件格式

`.csv` `.tsv` `.txt` `.json`

### 正则提取示例

| 场景 | 正则表达式 | 说明 |
|------|-----------|------|
| 提取冒号后值 | `:([^;]+)` | `xx:100;yy:200` → `100`, `200` |
| 提取引号内容 | `"([^"]+)"` | `name="张三"` → `张三` |
| 提取数字 | `(\d+)` | `ID:12345` → `12345` |
| 提取邮箱 | `[\w.-]+@[\w.-]+` | 匹配邮箱地址 |

### 计算列公式示例

| 公式 | 结果 |
|------|------|
| `{单价}*{数量}` | 金额计算 |
| `{姓}+{名}` | 姓名拼接 |
| `{分数}/100` | 百分比转换 |

### 隐私说明

**所有数据处理均在浏览器本地完成**，文件不会上传到任何服务器。适合处理敏感数据。

---

## 2. Traceability

**身份证模拟号生成器（测试数据）** — 基于 Vue 3 + Element Plus 的纯前端工具，可按地区、出生日期、性别等条件批量生成模拟身份证号，支持合法性校验与导出。

### 功能特性

| 功能 | 说明 |
|------|------|
| 地区选择 | 省/市/区三级联动，实时显示地区码，支持直辖市特殊处理 |
| 日期范围 | 可视化日历选择，默认 10~20 岁范围，跨度不超过 20 年 |
| 性别控制 | 可选男/女，或直接输入性别码（0-9） |
| 自定义参数 | 顺序号范围（如 `1-10,15`）、校验位筛选（如 `1,X,2`） |
| 合法校验 | 一键验证生成号码，保留符合 GB 11643-1999 标准的号码 |
| 数据导出 | 导出合法号码列表为 `.txt` 文件 |
| 批量渲染 | 大数据量分批渲染，避免页面卡顿 |

### 使用方式

- **在线使用**：直接访问 [GitHub Pages](https://xtar7.github.io/Galaxy-code/Traceability/)
- **本地使用**：下载 `Traceability/index.html` 和 `Traceability/data.json`，双击用浏览器打开
- **注意事项**：本地使用时需确保 `data.json` 与 `index.html` 在同一目录

### 技术栈

Vue 3 + Element Plus（CDN 引入），无需构建

### 免责声明

**本工具仅供学习与研究使用**，生成的身份证号码均为随机模拟数据，不具备任何法律效力。使用本工具所造成的任何后果，均由使用者自行承担，与作者无关。


---

## 3. Pentest Command Builder Pro

**渗透测试命令生成器 / 速查手册** — 纯前端、无框架、零构建，浏览器直接打开即用。基于"Top 10 攻击手法"分层组织 26 个工具，输入目标/参数即生成可直接复制的命令行，覆盖从信息收集到后渗透的完整链路。

### 功能特性

| 模块 | 说明 |
|------|------|
| 信息收集 | DNS 侦察（dig/dnsrecon/fierce）、WHOIS/RDAP 查询、子域名枚举 |
| 端口扫描 | Nmap 复合扫描（时序/分片/诱饵等 WAF 规避）、Nmap HTTP 脚本扫描 |
| 漏洞扫描 | Nikto、Nuclei 模板扫描（含 WAF 规避选项） |
| 注入攻击 | SQLMap 全阶段/批量注入、目录路径枚举 |
| 口令爆破 | Hydra、John the Ripper、Hashcat |
| 漏洞利用 | Metasploit 模块、Msfvenom、反弹 Shell、木马生成（一句话/免杀/JSP/内存马/加密马） |
| 后渗透 | Mimikatz、LinPEAS/WinPEAS 枚举 |
| 网络与传输 | Netcat、cURL、Wget 下载器 |
| 编码解码 | 常用编码/哈希/加解密速查工具箱 |
| Web 手工测试 | 报文转 cURL、JWT 工作台（alg:none / HS256 弱密钥）、Payload 变体器（WAF 绕过变体批量生成）、JSONP/CORS 探测 |
| 知识库 | Payload 速查库（XSS/SQLi/路径穿越/SSTI/命令注入/SSRF/XXE 等 12 类 118 条）、速查手册（提权清单/CVE/默认口令/WAF 绕过等）、实用小工具（IP/子网/Unix 时间戳） |

### 特色

- **作战环境栏**：目标/端口一次填写，全站自动带入各工具表单，支持目标池管理与一键重置
- **收藏夹**：收藏生成的命令，可导出为 `.sh` / `.ps1`（含变量化 `TARGET`/`LHOST`）
- **明暗主题**：暖炭落日（暗）/ 纸本赤陶（亮）双色主题，一键切换

### 使用方式

- **在线使用**：直接访问 [GitHub Pages](https://xtar7.github.io/Galaxy-code/PentestCB)
- **本地使用**：下载整个 `PentestCB/` 目录，双击 `index.html` 用浏览器打开

### 免责声明

**本工具仅供授权安全测试与研究使用**，请勿用于未授权目标。使用者须对使用该工具产生的任何后果自行负责，与作者无关。

---

## 4. EZ 指纹规则生成器

**EZ 指纹规则生成器** — 纯前端单页工具，根据 PoC 插件需求填写指纹字段（名称、类型、关键特征等），一键生成可复制到 PoC 插件的指纹规则 JSON 数据。

### 使用方式

- **在线使用**：直接访问 [GitHub Pages](https://xtar7.github.io/Galaxy-code/finger)
- **本地使用**：下载 `finger/index.html`，双击用浏览器打开

---

## 5. OpenRouter 免费模型速查

**OpenRouter 免费模型速查** — 自动抓取 [OpenRouter](https://openrouter.ai) 上全部免费（输入/输出 $0 定价）模型并展示：左侧提供商卡片筛选、搜索、每页 10/20/50 分页、一键复制 curl 调用示例、跳转 OpenRouter 详情页。数据经 Node.js 后端代理 + 文件缓存（15 分钟自动刷新），前端为纯 HTML/CSS/JS 卡片画廊。

### 功能特性

| 功能 | 说明 |
|------|------|
| 自动抓取 + 缓存 | 后端定时拉取 API，筛出 0 定价模型写入 `cache.json`，默认读缓存，页面提供手动刷新 |
| 统计 | 区分「完全免费」与「输入输出 $0 可试用」两类，并标注数据更新时间 |
| 提供商筛选 | 左侧卡片栏按提供商分组（含数量），点击即过滤 |
| 搜索 | 按模型名 / 提供商 / id 关键字即时过滤 |
| 分页 | 页脚页码（省略号收敛）+ 每页 10/20/50 切换，默认 10 条 |
| 复制调用示例 | 每个模型可一键复制带 `Authorization` 的 curl 命令 |
| 跳转详情 | 外链到 `openrouter.ai/models/{canonical_slug}` |

### 使用 Tips

需要本地或服务器上跑 Node 服务（OpenRouter API 不支持浏览器跨域直连，纯静态页拿不到数据）：

- 自行将 `or-free-models/` 目录下载到本地或服务器
- 运行（无第三方依赖）：

```bash
node server.js   # 默认 http://localhost:3000，可用 PORT 环境变量改端口
```

---

---

## 6. 系统软件清理工具

**系统软件及孤儿数据清理工具** — 扫描已安装软件与残留数据，模糊匹配后识别孤儿文件，支持回收站删除或永久删除。Python 3.8+，仅标准库（可选 `psutil`/`send2trash`/`pywin32`）。

### 功能特性

| 模块 | 功能 |
|------|------|
| 多维度扫描 | Windows 注册表、Program Files 文件系统、Winget/Scoop/Chocolatey 包管理器 |
| 应用数据扫描 | LOCALAPPDATA、APPDATA、PROGRAMDATA，支持自定义路径 |
| 智能对比 | 自动匹配已安装软件与残留数据，字符串相似度模糊匹配，按大小排序 |
| 安全清理 | 回收站删除（可恢复）、直接删除（需管理员）、演习模式（只分析不删） |
| 权限管理 | 自动请求管理员权限，支持 icacls 强制修改权限 |

### 使用方式

```bash
# 用 uv 创建虚拟环境
uv venv

# 图形界面（需管理员权限）
.venv\Scripts\python.exe main.py

# 命令行扫描（演习模式）
.venv\Scripts\python.exe main.py --cli --scan --dry-run

# 扫描并自动清理
.venv\Scripts\python.exe main.py --cli --scan --clean --auto
```

- **快速启动**：双击 `clean-tmp/run_cleaner.bat` 或 `run_cleaner.ps1`（右键"以管理员身份运行"）
- **演习模式**：首次使用建议 `--dry-run`，确认结果后再实际删除

### 架构

```
main.py                — 启动入口（GUI / CLI）
app_cleaner.py         — 核心逻辑（扫描器 / 对比分析 / 清理执行）
app_cleaner_gui.py     — tkinter 图形界面
run_cleaner.bat        — Windows 批处理启动
run_cleaner.ps1        — PowerShell 启动
```

---

## 7. HashDock 文件完整性校验

**HashDock · 文件完整性校验** — 单文件 Web 工具（`index.html` 直开），定位：文件哈希计算与完整性复核。支持单文件及批量文件 SHA-256 校验、清单导入导出、文件前后哈希比较与校验结果汇总。Web 版使用浏览器加密 API（Web Crypto 分块读取）；本地版能力（目录批处理、大文件分块、离线复核）以命令行参考形式内置。

### 功能特性

| 功能 | 说明 |
|------|------|
| 批量 SHA-256 | 单文件 / 批量选择即算，Web Crypto 256KiB 分块读取，全程本地不上传 |
| 清单导入导出 | 兼容 `sha256sum` 双空格格式；导出产物可直接被 `sha256sum -c` 复核 |
| 前后哈希比较 | 「基准清单」（期望值）+「前后基线」（操作前导出值）双列自动比对 |
| 结果汇总 | 统计卡（一致 / 不一致 / 缺失 / 变更 / 失败）+ 一键导出 TSV 汇总 |

### 使用方式

浏览器直接打开 `HashDock/index.html` 即可。典型前后对比流程：操作前导出清单 → 执行操作 → 重新计算 → 载入基线比对 → 导出 TSV 归档。

### 可信性边界（重要）

> 哈希相同可以支持文件内容一致性的判断，但**不能单独证明文件来源可信或文件从未被篡改**；可信基准和清单本身也需要保护（离线存放、独立渠道分发、签名、双人保管）。

### 本地版 / 命令行参考

```bash
sha256sum ./* > manifest.txt && sha256sum -c manifest.txt   # 生成 + 复核
find /path/to/dir -type f -exec sha256sum {} + > manifest.txt   # 目录批处理（GB 级）
```

---

## 快速导航

- [返回顶部](#galaxy-code--代码与工具集合)
- [查看目录](#目录)

---

## 关于本仓库

- **部署方式**：GitHub Pages（自动部署 `main` 分支根目录）
- **项目结构**：工具存放在独立子文件夹中，每个工具一个目录
- **添加新工具**：在子目录新建文件夹放入工具文件，更新本 README 目录表即可
- **技术栈**：以 HTML/CSS/JS 前端工具为主，也包含 Python 等其他语言的本地工具

## License

本项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可。

- **允许**：个人学习、研究、非商业使用
- **不允许**：商业用途、二次授权
- **要求**：署名、衍生作品须相同许可
