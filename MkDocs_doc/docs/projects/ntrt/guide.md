# 核心模块指南

本文从工程视角梳理 NTRT 项目的关键模块及其协作方式，帮助你快速定位“该改哪里、该看哪里”。

---

## 1. DataCleaner

| 属性 | 说明 |
| --- | --- |
| `BATCH_SIZE` | 控制单轮处理的记录数量 |
| `DEFAULT_DB_KEY` | 从 `session_dict` 选择要使用的数据库 |
| `cleaning_plan` | 描述每个字段的模型、过滤条件、处理函数 |

### 常用方法
- `run()`：主入口，串联查询 → 处理 → 写入，并打印统计信息
- `_process_breadth_search()`：将项目/文章信息整合成统一结构
- `_process_cited_articles()`：按 `object_id` 合并引用文献
- `_clean_dataset()`：通用批处理骨架，负责分页、统计、事务

> 扩展新的字段时，只需在 `cleaning_plan` 中追加条目并实现 `_process_xxx`。

---

## 2. ORM 模型

位于 `application/NsfcTopicRcmdModels.py`：

| 模型 | 表 | 主要字段 | 说明 |
| --- | --- | --- | --- |
| `NsfcTopicRcmdTaskList` | `nsfc_topic_rcmd_task_list` | `breadth_search` | 存放广度搜索结果（项目/文章集合） |
| `NsfcTopicRcmdTaskTopicList` | `nsfc_topic_rcmd_task_topic_list` | `cited_articles` | 主题维度的引用列表 |
| `NsfcTopicRcmdTaskAppInfo` | `nsfc_topic_rcmd_task_app_info` | `cited_articles` | 项目应用维度的引用列表 |

对应的 `*Model`（继承 `CleaningModelMixin`）提供：
- `fetch_records_for_cleaning()`：根据字段和附加过滤条件批量查询
- `batch_update_field()`：批量写回字段，自带事务控制

---

## 3. BaseCRUD & session_dict

- `BaseCRUD` 封装通用的增删改查操作，包括批量创建、条件更新、分页查询等。
- `session_dict` 在模块导入时按 `application.settings.DATABASES` 创建所有 `SessionLocal`，这样在运行时只需指定别名即可。

> 若要添加新数据库，只需在 `settings.py` 中加入条目即可自动生成 Session。

---

## 4. 字段处理策略

### breadth_search
- 标准化项目字段：`unit_name -> project_unit`、`leader_name -> project_leader` 等
- 处理 `apply_code`、`project_keyword` 等复合字段
- 兼容项目/文章两类实体，最终输出统一字典

### cited_articles
- 输入为 JSON 数组，输出为以 `object_id` 为键的字典
- 根据 `object_type` 决定是否套用 `_standardize_project_info`
- 忽略缺少 `object_id` 或 JSON 结构异常的记录

> 所有处理函数均返回新的对象，避免在原始记录上就地修改。

---

## 5. 扩展指南

| 需求 | 推荐做法 |
| --- | --- |
| 批量处理更多字段 | 在 `cleaning_plan` 中新增条目，复用 `_clean_dataset` |
| 切换数据库 | 在实例化 `DataCleaner` 前调整 `DEFAULT_DB_KEY`，或新增参数 |
| 增加日志/监控 | 在 `_clean_dataset` 中插入钩子，或扩展 `print` 为标准日志模块 |
| 集成到其它系统 | 将 `DataCleaner` 封装成函数/类，对外暴露 `run()` 即可 |

---

## 6. FAQ

- **如何跳过某个任务？**  
  临时注释 `cleaning_plan` 中对应项，或添加开关变量。

- **如何控制事务粒度？**  
  修改 `BATCH_SIZE`，或在 `batch_update_field` 中调整 `is_commit` 逻辑。

- **如何定位出错记录？**  
  在 `_process_records` 中加入更多调试信息，例如打印 `record_id`、字段值。

更多示例可参考 [使用示例](examples.md)。*** End Patch

