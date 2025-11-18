# 现用库/插件/工具一览

## MkDocs + mkdocs-material：

静态站生成、导航/搜索/明暗模式 UI、.md-button 等组件。

## mkdocstrings[python] + autorefs

解析 Python 模块 docstring，生成 API 参考并支持文内交叉引用。

## pymdown-extensions

### admonition / pymdownx.details：

折叠式“最近更新”等提示框。

### pymdownx.highlight：

代码高亮与行号。

### pymdownx.tabbed：

标签页内容（尚未大量使用，可随时启用）。

## Mermaid (extra_javascript)：

在 Markdown 内直接描述架构/流程图，浏览器端渲染。

## 自定义资源

### stylesheets/custom-nav.css：

多层导航的字号/间距/颜色控制。


### stylesheets/theme-overrides.css：

Hero、卡片、深色模式、表格和 TOC 视觉升级。

### javascripts/init-mermaid.js：

初始化 Mermaid，启用 securityLevel: "loose" 以支持文档中的链接。

## 主题配置扩展

### 自定义字体（Inter / JetBrains Mono）和调色板；夜间/日间切换按钮。

### Material search 插件（中文 + 英文分词）。