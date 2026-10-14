# HeaderScope · HTTP 安全头审计

单文件 Web 应用（`index.html`，无构建、无依赖、浏览器直接打开），定位：**把 HTTP 安全配置检查做成真正可用的审计工具**。粘贴或导入脱敏后的 HTTP 响应头，逐项审计响应头与 Cookie 安全配置，导出 Markdown / JSON 报告。

全程在浏览器本地运行：**不发起任何网络请求、不上传数据**。

风格沿用 DataForge 家族：浅色主题、`max-width:1400px` 容器、卡片 + 标签页布局（输入响应头 / 部署上下文 / 审计结果），原生 SVG 图标，无主题切换（统一浅色）。

## 功能

| 功能 | 说明 |
|---|---|
| 输入 | 粘贴原始 HTTP 报文 / DevTools 导出 / curl 抓包文本，或导入脱敏 `.txt`/`.log` 文件；自动识别头行并解析 `Set-Cookie` 属性 |
| 响应头检查 | CSP、HSTS、MIME 类型保护（`X-Content-Type-Options`）、Referrer-Policy、Permissions-Policy、点击劫持防护（`X-Frame-Options` / `frame-ancestors`） |
| Cookie 检查 | `Secure`、`HttpOnly`、`SameSite` 三属性逐 Cookie 判定 |
| 判定依据 | 每条发现给出**适用条件 + 为什么这样判**，而不只是「缺某个头」；含风险级别、建议配置（点击复制）与 MDN 官方参考链接 |
| 上下文感知 | 填入站点 URL / 敏感 Cookie 名单后，HSTS、Cookie 检查的严格度随真实部署条件变化 |
| 报告导出 | 一键导出 Markdown / JSON（含生成时间、推断协议、Cookie 明细、全部发现） |

## 差异化：不止打勾

HeaderScope 的核心不是「有没有 X-Frame-Options」，而是**解释结果在什么条件下成立**：

- **HSTS**：结论强依赖是否已启用 HTTPS。站点为 HTTP 时 HSTS 不适用（先迁 HTTPS 再下发）；已 HTTPS 却未下发才判为高危缺口；`max-age` / `includeSubDomains` 不足则降级为需关注。
- **CSP**：不能只看头是否存在。`'unsafe-inline'`、通配符来源会让「有 CSP」名存实亡；`frame-ancestors` 白名单过宽同样告警。
- **Cookie**：是否承载会话决定严重度。普通偏好 Cookie 缺 `SameSite` 只是低优先级建议；会话 Cookie 缺 `HttpOnly`/`Secure` 才升级为高危。

## 使用方式

1. 浏览器打开 `HeaderScope/index.html`
2. 在「输入响应头」标签页粘贴脱敏响应头（或点右上角「载入示例」看一个含会话 Cookie 的 HTTPS 样例）
3. 可选：切到「部署上下文」标签页填站点 URL / 敏感 Cookie 名称，让判定贴合实际
4. 「开始审计」→ 切到「审计结果」标签页按风险排序查看发现，用筛选 chips 只看未达标项
5. 「导出 Markdown」/「导出 JSON」归档报告

快捷键：在输入框内 `Ctrl/Cmd + Enter` 快速审计。

## 边界与说明

- 本工具**不做**任意目标自动扫描、不发任何出站请求（本地版后续才加入「授权范围内」的 HTTP 请求测试）。当前版本完全离线。
- 结果基于静态响应头推断，**不能替代**针对真实站点的完整安全评估；CSP / HSTS 是否「达标」需结合实际脚本来源与部署环境人工复核。
- 参考链接指向 MDN Web Docs。

## 实现说明

- 单文件 `index.html`（内联 CSS/JS），`file://` 直开即用的前提是无运行时 `fetch` — 全部逻辑自包含
- 响应头解析：正则识别 `Name: value` 头行，忽略状态行 / 折叠续行；`Set-Cookie` 单独按 `;` 拆属性解析
- 上下文推断：协议优先取用户填写的 URL，否则按「是否出现 HSTS 头」推断；推断不确定时检查项标记为「需确认部署」而非武断打红
- 状态为会话内存对象（刷新即清）；无 localStorage 使用
- CSS 令牌与 DataForge 一致（`:root` 浅色），无暗色主题；颜色全部走变量，无硬编码色值
