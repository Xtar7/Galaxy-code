# HashDock · 文件完整性校验

单文件 Web 应用（`index.html`，无构建、无依赖、浏览器直接打开），定位：**文件哈希计算与完整性复核**。

## 功能

| 功能 | 说明 |
|---|---|
| 单文件 / 批量 SHA-256 | Web Crypto API，**256KiB 分块读取**——GB 级大文件内存占用恒定，全程本地不上传 |
| 清单导入 / 导出 | 兼容 `sha256sum` 双空格格式（容忍单空格、`*` 二进制前缀会跳过）；导出产物可直接被 `sha256sum -c manifest.txt` 复核 |
| 前后哈希比较 | 「基准清单」（期望值）与「前后基线」（操作前导出值）双列对比：vs 基准 / vs 基线（变更） |
| 校验结果汇总 | 结果区顶部统计卡（一致 / 不一致 / 缺失 / 失败 / 变更）+ 一键导出 TSV 汇总（含状态列与时间戳） |

## 本地版 / 命令行参考

Web 版受浏览器文件访问限制（无法直接枚举目录）；目录批处理、离线复核与 GB 级大文件深度校验请用内置参考卡中的命令：

```bash
# 生成清单 + 复核（不符报 FAILED）
sha256sum ./* > manifest.txt && sha256sum -c manifest.txt
# macOS
shasum -a 256 ./* > manifest.txt
# 目录批处理（find 分块喂入）
find /path/to/dir -type f -exec sha256sum {} + > manifest.txt
# 前后对比：只重算基线中出现过的文件
awk '{print $2}' manifest_old.txt | while read -r f; do
  [ -f "$f" ] && sha256sum "$f"
done > manifest_now.txt
diff manifest_old.txt manifest_now.txt   # 有输出即存在变更
```

## ⚠️ 可信性边界（重要）

> 哈希相同**可以支持文件内容一致性的判断**，但**不能单独证明文件来源可信或文件从未被篡改**。
> 可信基准和清单本身也需要保护：离线存放、独立渠道分发、签名（如 `gpg --sign manifest.txt`）、双人保管。

## 使用流程（前后对比典型场景）

1. 操作前：选择文件 → 计算 → **导出清单**（作为基线 / 基准）
2. 执行操作（拷贝、解压、补丁、镜像制作…）
3. 操作后：再次选择文件 → 计算
4. 粘贴基线到「⏪ 前后基线」载入，粘贴期望值到「📋 清单」载入 → 结果区双列自动比对并汇总
5. 导出 TSV 汇总归档

## 实现说明

- 单文件 `index.html`（内联 CSS/JS），`file://` 直开即用的前提是无运行时 fetch——全部功能自包含
- 哈希计算：`crypto.subtle.digest('SHA-256')` + `Blob.slice` 256KiB 分块（SubtleCrypto 无增量 API，分块读入后拼接，2GB+ 请走命令行）
- 状态为会话内存对象（切标签页不丢，刷新即清）；仅主题偏好走 localStorage（`hashdock-theme`）
- 颜色走 CSS 令牌（`:root` 亮色默认 / `[data-theme="dark"]` 暗色），无硬编码色值
