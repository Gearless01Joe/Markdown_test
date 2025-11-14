# 国自然选题推荐 - 使用指南

## 安装

```bash
pip install -r requirements.txt
```

## 基本使用

### 初始化

```python
from data_cleaner import DataCleaner

cleaner = DataCleaner()
```

### 执行清洗任务

```python
cleaner.run()
```

## 配置

可以通过修改 `DEFAULT_DB_KEY` 和 `BATCH_SIZE` 来调整配置。

## 常见问题

### Q: 如何处理导入错误？

A: 确保所有依赖都已安装，检查 `application.settings` 配置是否正确。

