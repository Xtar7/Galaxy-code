# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Node.js 后端（Express 或同等最小 HTTP 服务）作为 OpenRouter API 代理 + 缓存层；前端为简单 HTML/CSS/JS 单页，与仓库内其他项目（Traceability、DataForge、PentestCB 等）同为静态页面风格。

## Users

公开使用者：任何人在配置 LLM 工具、写 prompt 或选型时，想快速查 OpenRouter 上当前可用的免费（$0 定价）模型。

## Product Purpose

一个公开可分享的 Web 页面，展示 OpenRouter 上所有免费（free）模型，支持筛选/查找；数据来自 OpenRouter 官方 `/api/v1/models` 接口，由 Node.js 后端代理并缓存（因浏览器跨域限制无法直连）。成功标准：打开页面即可看到当前全部免费模型列表，且数据可手动刷新或定时缓存更新。

## Positioning

比直接打开 OpenRouter 网站或原始 API 更轻：只看免费模型，一屏可达，无需注册 OpenRouter 账号，无付费模型干扰。

## Operating Context

- 后端定时（或手动触发）拉取 `https://openrouter.ai/api/v1/models`，筛选出定价为 0 的模型并写入本地缓存（文件即可）
- 前端读取缓存数据渲染列表，展示"数据更新于 xx 时间"
- 使用者可能直接分享 URL 给他人，无后端登录/鉴权需求

## Capabilities and Constraints

- 必须经过服务端代理，纯静态页无法绕过 OpenRouter API 的 CORS 限制
- 需标注数据缓存时间，明确非实时
- 筛选字段（上下文长度、提供商、名称搜索）为确认的最小功能集；排序、点击跳转详情页等为待确认扩展项

## Evidence on Hand

- OpenRouter 提供公开 REST 接口 `/api/v1/models`，无需鉴权即可读取模型列表和定价信息（待实际验证字段结构）
- 仓库内已有多个同类静态页面项目可参考实现风格

## Product Principles

1. 免费模型是唯一筛选条件，不为付费模型让路
2. 数据必须标注更新时间，不伪装成实时
3. 单页、无鉴权、可直接分享 URL
4. 轻量优先：后端只做代理+缓存，不过度设计
