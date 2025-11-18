# 架构设计

NTRT 项目采用“调度层 + ORM 封装层 + 字段处理层”三段式结构，确保清洗逻辑可维护、可扩展。

---

## 1. 组件总览

```
┌────────────┐    ┌──────────────┐    ┌──────────────┐
│ DataCleaner│ -> │ CleaningModel│ -> │ BaseCRUD/ORM  │
└────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        │                   │                   └── SQLAlchemy Session
        │                   └── NsfcTopicRcmd* 模型
        └── 字段处理器 (_process_*)
```

| 层级 | 说明 | 关键对象 |
| --- | --- | --- |
| 调度层 | 以事务方式串联查询、处理、写入 | `DataCleaner.run()` |
| ORM 封装层 | 将不同表模型统一为 CRUD 接口 | `CleaningModelMixin`、`BaseCRUD` |
| 字段处理层 | 针对特定 JSON 字段的标准化逻辑 | `_process_breadth_search`、`_process_cited_articles` |

---

## 2. 数据流

1. **查询阶段**：`_fetch_records_with_condition` 根据额外过滤条件批量获取待处理数据。
2. **处理阶段**：为每条记录调用 `_process_breadth_search` / `_process_cited_articles`，生成目标结构。
3. **更新阶段**：`batch_update_field` 批量写回 MySQL，同时统计成功/跳过数量。
4. **事务控制**：每批次提交一次，可根据需要调整 `BATCH_SIZE` 或将事务包装到更大粒度。

---

## 3. 关键模块

| 模块 | 作用 | 亮点 |
| --- | --- | --- |
| `DataCleaner` | 清洗任务 orchestrator | 提供统一日志、批量遍历、错误统计 |
| `NsfcTopicRcmdTask*Model` | ORM 映射 + 清洗辅助方法 | `fetch_records_for_cleaning`、`batch_update_field` |
| `BaseCRUD` | 通用 CRUD 封装 | 支持批量插入、更新、统计、事务控制 |
| `base_mysql.session_dict` | 会话工厂 | 支持多数据库别名，运行期自由切换 |
| `application.settings` | 环境配置 | 同时提供测试、生产、SaaS 等多个连接 |

---

## 4. 字段处理策略

### breadth_search
- 合并 `project_addition` 与 `article_addition`
- 项目字段统一命名（如 `unit_name -> project_unit`）
- 处理关键词列表、`apply_code` 结构

### cited_articles
- 接受数组形式的引用列表
- 以 `object_id` 为主键构建字典，区分项目/文章类型
- 对项目引用补全标准字段

> 所有 processor 函数都返回新的 Python 对象，避免直接修改原始引用。

---

## 5. 可扩展点

| 场景 | 建议做法 |
| --- | --- |
| 新增字段清洗 | 在 `cleaning_plan` 中追加任务 + 实现 `_process_xxx` |
| 扩展目标表 | 继承 `CleaningModelMixin` 并设置 `model` 属性 |
| 引入外部 JSON 规则 | 在 `_process_*` 中加载配置或传入回调 |
| 切换数据库 | 通过 `DEFAULT_DB_KEY` 或构造函数参数切换 `session_dict` |

---

## 6. 运行模式

| 模式 | 说明 |
| --- | --- |
| 手动脚本 | `python -m data_cleaner` 或嵌入到其他任务流 |
| 定时任务 | 借助 Airflow / Cron / APScheduler 周期执行 |
| 服务化 | 将 `DataCleaner` 封装为 Celery 任务或 FastAPI 接口 |

---

## 7. 依赖关系

- **SQLAlchemy**：模型声明、Session 管理、JSON 运算
- **MySQL JSON 函数**：`json_contains_path`、`json_type`
- **本地 JSON 文件**：业务规则、示例数据，位于根目录若干 `.json`

在迁移到其他数据库/版本前，需要评估 JSON 函数兼容性。

