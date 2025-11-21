# 项目文档

> 项目文档中心涵盖所有在研/已部署项目的知识资产，统一入口、统一结构、统一指引。

<div class="project-intro">
  <p>每个项目默认包含九大模块：从“概述”到“更新日志”，覆盖研发、部署、运维的全生命周期。以下卡片提供快速跳转。</p>
  <div class="project-intro__chips">
    <span class="chip">2 个重点项目</span>
    <span class="chip">18+ 模块</span>
    <span class="chip">统一文档模板</span>
  </div>
</div>

## 项目列表

<div class="project-grid">
  <article class="project-card">
    <header>
      <div>
        <p class="project-card__eyebrow">数据清洗 · 国自然选题推荐</p>
        <h3>NTRT 项目</h3>
      </div>
      <span class="project-badge">Data Cleaner</span>
    </header>
    <p>围绕 `DataCleaner`、`BaseCRUD`、`cleaning_plan` 的批量清洗流水线，聚焦数据库同步、字段标准化与调度集成。</p>
    <div class="project-meta">
      <div>
        <strong>最近更新</strong>
        <p>2025-01-10</p>
      </div>
      <div>
        <strong>负责人</strong>
        <p>LZD · 数据建设组</p>
      </div>
      <div>
        <strong>状态</strong>
        <p>已部署</p>
      </div>
    </div>
  </article>

  <article class="project-card">
    <header>
      <div>
        <p class="project-card__eyebrow">爬虫 · RCSB PDB</p>
        <h3>RCSB PDB 项目</h3>
      </div>
      <span class="project-badge project-badge--alt">Crawler</span>
    </header>
    <p>基于 Scrapy + FieldFilter + Pipeline + Redis 的蛋白质数据库采集方案，提供 Playwright 中间件与任务监控。</p>
    <div class="project-meta">
      <div>
        <strong>最近更新</strong>
        <p>2025-01-05</p>
      </div>
      <div>
        <strong>负责人</strong>
        <p>HJL · 数据建设组</p>
      </div>
      <div>
        <strong>状态</strong>
        <p>持续迭代</p>
      </div>
    </div>
  </article>
</div>

## 添加新项目

1. 在 `docs/projects/` 下创建项目目录，并复制上述九个模板文件。
2. 根据实际内容填写 Markdown，或运行脚本自动生成 API/示例章节。
3. 更新 `mkdocs.yml` 中 “项目文档” 的 `nav`，保持名称与顺序统一。
4. 在 `projects/index.md` 中增加对应卡片，使首页导航保持一致。

