# OpenRouter 免费模型速查

一个自动抓取 [OpenRouter](https://openrouter.ai) 上全部免费（输入/输出单价为 $0）模型的 Web 页面。数据经 Node.js 后端代理并缓存，前端以卡片画廊形式展示，支持按提供商筛选、搜索、分页，可一键复制 curl 调用示例或跳转到 OpenRouter 详情页。

> 因 OpenRouter API 未对浏览器开放 CORS，纯静态页无法直接抓取数据，所以需要一个最小后端做代理 + 缓存。

## 功能

- **自动抓取 + 缓存**：后端定时（15 分钟）拉取 `openrouter.ai/api/v1/models`，筛出 `pricing.prompt === "0" && pricing.completion === "0"` 的模型写入本地 `cache.json`；前端默认读缓存，页面提供「刷新」按钮强制重新抓取。
- **总数统计**：区分「完全免费」和「输入输出 $0 可试用」两类，并在页面标注数据更新时间。
- **提供商筛选**：左侧卡片栏按提供商分组（含各提供商模型数量），点击即过滤。
- **搜索**：按模型名 / 提供商 / id 关键字即时过滤。
- **分页**：页脚显示页码（省略号收敛），可切换每页 10 / 20 / 50 条，默认每页 10 条。
- **复制调用示例**：每个模型可一键复制带 `Authorization` 的 curl 命令。
- **跳转详情**：外链到 `openrouter.ai/models/{canonical_slug}`（已验证使用 `canonical_slug` 并去掉 `:free` 变体后缀、且保留原始斜杠，否则 OpenRouter 前端会渲染空页 / "Author Not Found"）。

## 运行

无第三方依赖，Node.js 直接跑：

```bash
node server.js
# 打开 http://localhost:3000（PORT 可通过环境变量覆盖）
```

`package.json` 也提供了 `npm start` 等价命令。

## 文件结构

| 文件 | 说明 |
|---|---|
| `server.js` | 最小 Node 后端：代理 API、筛选、文件缓存、静态托管，零依赖 |
| `index.html` | 前端单页：卡片画廊、搜索、筛选、分页、复制 |
| `cache.json` | 运行时生成的缓存文件（已 gitignore，不入库） |
| `package.json` | 元信息 + `start` 脚本 |
| `DESIGN.md` | 设计决策记录（impeccable 流程） |

## 说明

- 免费判定以 `pricing.prompt` 和 `pricing.completion` 是否均为 `"0"`（或缺省）为准；当前 OpenRouter 上所有免费模型都明确标记了 0 单价，因此「$0 可试用」类暂时为空，一旦 API 返回此类模型会自动归入该类。
- 每 15 分钟自动后台刷新一次缓存；也可随时点页面上「刷新」按钮立即重新抓取。
