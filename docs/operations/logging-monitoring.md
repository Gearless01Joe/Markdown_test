# 日志与监控指南

## 日志策略

- **结构化日志**：统一使用 JSON 或半结构化格式，字段包含 `timestamp`, `level`, `project`, `module`, `trace_id`.
- **等级划分**：`INFO`（流程节点）、`WARNING`（可恢复）、`ERROR`（失败）、`CRITICAL`（阻塞）。
- **采集路径**：
  - 本地开发：`logs/<project>.log`
  - 测试/生产：Filebeat → Logstash → Elasticsearch/Kibana

```python
import structlog

logger = structlog.get_logger().bind(project="rcsb-pdb")

logger.info("pipeline_start", batch_id=batch.id)
logger.warning("retry_spider", url=url, retry=retry)
logger.error("persist_failed", exc_info=True)
```

## 监控指标

| 类别 | 指标 | 说明 |
| --- | --- | --- |
| 采集 | `spider.requests_per_minute` | Scrapy StatsExporter |
| 清洗 | `datacleaner.jobs_success_rate` | DataCleaner Pipeline |
| 存储 | `pipeline.mongo_latency_ms` | Mongo/文件落盘耗时 |
| 队列 | `redis.queue_depth` | 不同优先级任务数量 |

- 推荐使用 Prometheus + Grafana；Scrapy/Python 进程可通过 `prometheus_client` 暴露指标。
- 关键指标需配置告警，阈值写入 `docs/operations/logging-monitoring.md` 方便查阅。

## 分布式追踪

- 采用 `trace_id`（UUID）贯穿 Spider → FieldFilter → Pipeline → DataCleaner。
- 与 APM（如 SkyWalking、Jaeger）整合，构建端到端链路。
- 在文档或 FAQ 中附 trace 示例，便于培训与排障。

## 最佳实践

1. 重要函数外层使用装饰器记录执行时间与输入摘要。
2. 异常捕获后写日志并附 `context`，但避免输出敏感数据。
3. 每次发布在 Grafana 创建新面板或对现有面板做标注，方便回溯。
4. 将日志、指标的告警策略同步到值班手册与 PagerDuty。

> 若新增监控组件，请同步更新此文档和 `resources/roadmap.md`，确保改造进度可追踪。*** End Patch}]}`

