# Antigravity AI PWA 离线占星支持规格 (Round 28)

## 动机
在网络不好的印度乡村或冥想环境中，如果用户想算一个盘，需要依赖网络 API 请求，这是一种倒退（桌面版 JHora 可以离线）。

## 技术实现路径
1. 目前引擎是 Python 后端。要实现纯离线，我们要么将核心通过 Pyodide 编译成 WebAssembly (Wasm) 跑在浏览器里。
2. 或者，为客户端开发一套纯 JS 的降级星历算法库 (如使用 moshier ephemeris)，能在没有后端时勉强算出 D1。
3. Service Worker：拦截 `/api/chart`。如果处于离线且有 Wasm，则本地计算；否则返回报错提醒。

## 结论
完全 WASM 化成本过高，建议保持目前的 B/S 架构，优先追求 Web 界面的丝滑度。但可以缓存用户算过的“历史命盘”。

## 状态
`部分成立`
