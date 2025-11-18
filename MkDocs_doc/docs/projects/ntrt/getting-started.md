# 快速开始

本指南帮助你在 10 分钟内搭建 NTRT 数据清洗环境，并运行首个清洗任务。

---

## 1. 先决条件

| 组件 | 建议版本 | 说明 |
| --- | --- | --- |
| Python | 3.10+ | 建议使用虚拟环境 `.venv` |
| MySQL | 5.7+/8.0 | 需要具备 `nsfc_topic_rcmd_*` 系列表 |
| pip | 23+ | 需具备安装外网依赖能力 |
| Git | 2.30+ | 拉取仓库 |

> 如果链路受限，可提前配置公司制品库或镜像站。

---

## 2. 克隆与安装

```bash
git clone git@github.com:Gearless01Joe/Markdown_test.git
cd Markdown_test

# 准备虚拟环境
python -m venv .venv
.venv\Scripts\activate    # Windows

# 安装依赖
pip install -r code_liu/NTRT/requirements.txt
```

---

## 3. 配置数据库

默认配置位于 `code_liu/NTRT/application/settings.py`。根据环境修改：

```python
DATABASES = {
    'medicine': {
        'HOST': '192.168.1.243',
        'PORT': '3306',
        'USER': 'medpeer',
        'PASSWORD': 'medpeer',
        'NAME': 'medicine',
        'CHARSET': 'utf8mb4',
    },
    'medicine_test': {
        'HOST': 'localhost',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': '***',
        'NAME': 'medicine_test',
        'CHARSET': 'utf8mb4',
    },
}
```

推荐将敏感信息抽离为环境变量：

```bash
set NTRT_DB_HOST=192.168.1.243
set NTRT_DB_USER=medpeer
# 在 settings.py 中通过 os.getenv 读取
```

---

## 4. 运行清洗任务

```bash
cd code_liu/NTRT
python - <<'PY'
from data_cleaner import DataCleaner

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run()
PY
```

### 可选参数

目前 `DataCleaner` 通过常量控制批次与数据库：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BATCH_SIZE` | 100 | 单次查询/更新的记录数 |
| `DEFAULT_DB_KEY` | `medicine` | 对应 `session_dict` 的数据库别名 |

可在运行前直接修改常量或新增初始化参数。

---

## 5. 验证结果

1. **控制台**：观察“开始/完成”日志、每个字段的统计信息
2. **数据库**：检查目标表的 `breadth_search`、`cited_articles` 字段是否被标准化
3. **Git 状态**：确认未误修改配置或依赖

---

## 6. 常用命令

| 场景 | 命令 |
| --- | --- |
| 格式化 JSON 结果 | `SELECT JSON_PRETTY(breadth_search) ...` |
| 统计待处理数量 | `SELECT COUNT(*) FROM ... WHERE JSON_TYPE(...) = 'ARRAY'` |
| 切换数据库别名 | 编辑 `DEFAULT_DB_KEY` 或 `session_dict` |
| 调整批次大小 | 修改 `BATCH_SIZE` |

---

## 7. 遇到问题？

请参考 [故障排查](troubleshooting.md) 获取数据库连接、JSON 解析、事务回滚等常见问题的解决方案。*** End Patch

