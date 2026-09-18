// 最小 Node 后端：代理 OpenRouter API + 文件缓存，前端静态页
// 运行：node server.js  （无第三方依赖）
const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3000;
const CACHE_FILE = path.join(__dirname, "cache.json");
const REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 分钟自动刷新

function isFreeish(model) {
  const p = model.pricing || {};
  const prompt = p.prompt === "0" || p.prompt === undefined;
  const completion = p.completion === "0" || p.completion === undefined;
  return prompt && completion;
}

function fetchModels() {
  return new Promise((resolve, reject) => {
    https
      .get("https://openrouter.ai/api/v1/models", { headers: { "User-Agent": "openrouter-free-models/1.0" } }, (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          if (res.statusCode !== 200) return reject(new Error("OpenRouter HTTP " + res.statusCode));
          try {
            const arr = JSON.parse(data).data;
            resolve(arr.filter(isFreeish));
          } catch (e) {
            reject(e);
          }
        });
      })
      .on("error", reject);
  });
}

async function getModels(force) {
  if (!force) {
    try {
      const raw = JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
      const age = Date.now() - raw.updatedAt;
      if (age < REFRESH_INTERVAL_MS) return raw;
    } catch (_) { /* 缓存缺失或过期，继续抓取 */ }
  }
  const models = await fetchModels();
  const payload = { models, updatedAt: Date.now() };
  fs.writeFileSync(CACHE_FILE, JSON.stringify(payload, null, 2));
  return payload;
}

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon" };

http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://localhost");

    if (url.pathname === "/api/free-models" || url.pathname === "/api/refresh") {
      const payload = await getModels(url.pathname === "/api/refresh" || url.searchParams.get("force") === "1");
      res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
      res.end(JSON.stringify(payload));
      return;
    }

    let filePath = path.join(__dirname, url.pathname === "/" ? "index.html" : url.pathname);
    filePath = path.normalize(filePath);
    if (!filePath.startsWith(__dirname)) {
      res.writeHead(403);
      return res.end("Forbidden");
    }
    const ext = path.extname(filePath);
    fs.readFile(filePath, (err, buf) => {
      if (err) {
        res.writeHead(404);
        return res.end("Not Found");
      }
      res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
      res.end(buf);
    });
  } catch (e) {
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: String(e) }));
  }
}).listen(PORT, () => {
  console.log(`运行在 http://localhost:${PORT}`);
  getModels().catch((e) => console.error("首次抓取失败，将等待手动刷新:", e.message));
});
