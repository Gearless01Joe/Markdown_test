# 维护与故障处理

## 范围

- 日志采集与可观察性
- 运维报警与值班流程
- 常见问题排查与经验库
- 性能优化与容量规划

## 关联文档

| 主题 | 链接 |
| --- | --- |
| 日志与监控指南 | [logging-monitoring.md](logging-monitoring.md) |
| 通用排障手册 | [troubleshooting.md](troubleshooting.md) |
| 性能优化 | [guide/advanced/performance.md](../guide/advanced/performance.md) |

## 响应级别

- **S0**：生产数据不可用 → 15 分钟内响应，1 小时内给出缓解方案，所有沟通在应急群同步。
- **S1**：主要功能异常但有绕过方式 → 30 分钟响应，4 小时内修复或回滚。
- **S2**：非阻塞问题 → 纳入迭代计划，在维护日志登记。

> 遇到未覆盖的场景，请优先记录在「通用排障手册」，再安排专项改进。*** End Patch}]}`

