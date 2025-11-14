# Python 技术文档工具对比

## 检索能力对比

| 工具 | 搜索方式 | 函数签名检索 | 参数/返回值检索 | 源代码位置 | 评分 |
|------|----------|--------------|----------------|------------|------|
| **Sphinx** | 全文搜索 + 对象索引 | ✅ 优秀 | ✅ 优秀 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **MkDocs + Material** | lunr.js 客户端搜索 | ✅ 良好 | ✅ 良好 | ✅ 支持 | ⭐⭐⭐⭐ |
| **Docusaurus** | Algolia 集成 | ✅ 优秀 | ✅ 优秀 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **pydoc-markdown** | 基础搜索 | ⚠️ 一般 | ⚠️ 一般 | ✅ 支持 | ⭐⭐⭐ |
| **GitBook** | 全文搜索 | ⚠️ 一般 | ⚠️ 一般 | ❌ 不支持 | ⭐⭐⭐ |

## 层级结构支持对比

| 工具 | 多项目支持 | 多层级导航 | 多版本 | 多语言 | 评分 |
|------|-----------|-----------|--------|--------|------|
| **Sphinx** | ✅ intersphinx | ✅ 无限层级 | ✅ 支持 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **MkDocs + Material** | ✅ 插件支持 | ✅ 多层级 | ⚠️ 需插件 | ✅ 支持 | ⭐⭐⭐⭐ |
| **Docusaurus** | ✅ 原生支持 | ✅ 多层级 | ✅ 原生 | ✅ 原生 | ⭐⭐⭐⭐⭐ |
| **pydoc-markdown** | ⚠️ 需配置 | ✅ 支持 | ❌ 不支持 | ⚠️ 需配置 | ⭐⭐⭐ |
| **GitBook** | ✅ 多空间 | ✅ 多层级 | ✅ 支持 | ✅ 支持 | ⭐⭐⭐⭐ |

## 详细功能对比

### 1. Sphinx

**检索能力**：
- ✅ 内置全文搜索引擎
- ✅ 自动生成对象索引（genindex.html）
- ✅ 支持搜索函数名、类名、模块名
- ✅ 搜索结果直接链接到定义位置
- ✅ 支持搜索参数名和返回值

**层级结构**：
- ✅ 支持多项目（intersphinx）
- ✅ 无限层级 toctree
- ✅ 支持多版本文档
- ✅ 支持多语言

**示例配置**：
```python
# conf.py
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',  # 跨项目链接
    'sphinx.ext.viewcode',     # 查看源代码
    'sphinx.ext.search',       # 增强搜索
]

# 多项目配置
intersphinx_mapping = {
    'project1': ('https://project1.readthedocs.io/', None),
    'project2': ('https://project2.readthedocs.io/', None),
}
```

**适用场景**：
- 大型项目
- 需要深度检索
- 多项目整合
- 需要 PDF 输出

---

### 2. MkDocs + Material Theme

**检索能力**：
- ✅ lunr.js 客户端搜索
- ✅ 支持搜索函数签名
- ✅ 支持搜索参数和返回值
- ✅ 支持代码高亮搜索
- ⚠️ 搜索速度取决于文档大小

**层级结构**：
- ✅ 多层级导航
- ✅ 支持标签分组
- ✅ 支持多仓库插件（mkdocs-multirepo-plugin）
- ⚠️ 多版本需要额外配置

**增强搜索配置**：
```yaml
plugins:
  - search:
      lang: ['zh', 'en']
      prebuild_index: true  # 预构建索引，提升搜索速度
  - mkdocstrings:
      handlers:
        python:
          options:
            show_signature: true
            show_source: true
            show_root_heading: true
```

**适用场景**：
- 现代 UI 需求
- 快速迭代
- 团队协作
- 需要美观界面

---

### 3. Docusaurus

**检索能力**：
- ✅ Algolia DocSearch 集成（免费）
- ✅ 支持函数签名搜索
- ✅ 支持参数和返回值搜索
- ✅ 支持代码片段搜索
- ✅ 搜索结果高亮

**层级结构**：
- ✅ 原生多项目支持
- ✅ 多层级侧边栏
- ✅ 原生多版本支持
- ✅ 原生多语言支持
- ✅ 支持文档分类和标签

**Python 支持**：
```bash
npm install @docusaurus/init
npx @docusaurus/init init my-docs classic
# 然后集成 Python 文档生成工具
```

**适用场景**：
- 大型团队
- 需要强大搜索
- React 技术栈
- 需要多版本管理

---

### 4. pydoc-markdown

**检索能力**：
- ⚠️ 基础全文搜索
- ⚠️ 搜索功能相对简单
- ✅ 支持导出多种格式

**层级结构**：
- ✅ 支持多项目
- ✅ 自定义层级
- ⚠️ 需要手动配置

**特点**：
- 专注于 Python 文档
- 可导出 Markdown、HTML、PDF
- 配置相对复杂

---

### 5. GitBook

**检索能力**：
- ✅ 全文搜索
- ⚠️ 搜索功能中等
- ❌ 不支持源代码位置链接

**层级结构**：
- ✅ 多层级目录
- ✅ 多空间支持
- ✅ 多版本支持
- ✅ 多语言支持

**特点**：
- 在线编辑
- 团队协作功能强
- 商业化产品

---

## 针对你的需求的推荐

### 需求1：优秀的检索效果（函数输入输出和位置）

**最佳选择**：
1. **Sphinx** ⭐⭐⭐⭐⭐
   - 对象索引最完善
   - 搜索结果最精确
   - 直接链接到源代码位置

2. **Docusaurus + Algolia** ⭐⭐⭐⭐⭐
   - Algolia 搜索最强大
   - 支持模糊搜索
   - 搜索结果高亮

3. **MkDocs + Material** ⭐⭐⭐⭐
   - 搜索功能良好
   - 需要配置预构建索引提升性能

### 需求2：多层级结构（整个团队技术文档）

**最佳选择**：
1. **Sphinx + intersphinx** ⭐⭐⭐⭐⭐
   - 原生支持多项目
   - 无限层级
   - 跨项目链接

2. **Docusaurus** ⭐⭐⭐⭐⭐
   - 原生多项目支持
   - 多层级侧边栏
   - 文档分类功能

3. **MkDocs + multirepo-plugin** ⭐⭐⭐⭐
   - 插件支持多仓库
   - 多层级导航
   - 需要额外配置

## 综合推荐方案

### 方案 A：Sphinx（最推荐）

**优势**：
- ✅ 检索能力最强
- ✅ 多层级结构最完善
- ✅ 多项目支持最好
- ✅ 你已经在使用，学习成本低

**配置示例**：
```python
# conf.py - 多项目配置
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.search',
]

# 多项目映射
intersphinx_mapping = {
    'project1': ('../project1/docs', None),
    'project2': ('../project2/docs', None),
    'project3': ('../project3/docs', None),
}
```

### 方案 B：Docusaurus（如果团队接受 React）

**优势**：
- ✅ 搜索最强大（Algolia）
- ✅ 多层级结构完善
- ✅ UI 最现代
- ✅ 多版本管理原生支持

**劣势**：
- ❌ 需要 Node.js 环境
- ❌ 学习成本较高

### 方案 C：MkDocs + 增强配置（平衡方案）

**优势**：
- ✅ 配置简单
- ✅ UI 现代
- ✅ 搜索功能良好（需优化）

**增强配置**：
```yaml
plugins:
  - search:
      prebuild_index: true
      lang: ['zh', 'en']
  - mkdocstrings:
      handlers:
        python:
          options:
            show_signature: true
            show_source: true
            show_root_heading: true
            show_root_toc_entry: true
```

## 检索功能增强建议

### 1. 使用 Algolia DocSearch（免费）

适用于任何静态站点生成器：
- 注册 Algolia DocSearch
- 提交你的文档站点 URL
- 获得强大的搜索功能

### 2. 使用 Elasticsearch（自建）

适用于大型团队：
- 自建搜索服务
- 完全控制搜索逻辑
- 支持复杂查询

### 3. 使用 Typesense（开源替代）

适用于需要强大搜索但不想用 Algolia：
- 开源搜索引擎
- 类似 Algolia 的 API
- 可以自托管

## 总结

**针对你的需求（检索 + 多层级）**：

1. **首选**：继续使用 **Sphinx**，配置 intersphinx 实现多项目整合
2. **次选**：**Docusaurus**，如果团队接受 React 技术栈
3. **备选**：**MkDocs + 增强配置**，如果更看重 UI 和易用性

**建议**：先完善 Sphinx 的多项目配置，因为：
- 你已经在使用
- 检索能力最强
- 多层级支持最好
- 学习成本最低

