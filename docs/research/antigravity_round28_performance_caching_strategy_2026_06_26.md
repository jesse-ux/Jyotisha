# Antigravity AI 引擎性能与缓存策略 (Round 28)

## 为什么需要缓存
目前每一次点击合婚或者查询一个月历，都会导致后端重新跑一遍全盘算法甚至星历遍历。

## 性能瓶颈点
1. `panchanga_range` 请求一个月的吉日，会造成极高的循环运算负荷。
2. 如果一千个用户同时算今天的月历，服务器会扛不住。

## 优化策略
1. 对不依赖于个人生辰的数据（如某地当月的日出、月相、节假日），必须在内存或 Redis 做 `lat_lon_month` 级别的 Cache。
2. 为 `/api/panchanga_range` 添加 HTTP `Cache-Control: public, max-age=86400`。
3. 个人命盘查询应通过生辰字符串做 Hash 缓存。

## 状态
`未成立`
