# 爬虫模块 - API 参考

## 基础爬虫类

### BaseSpider

所有爬虫的基类，提供公共功能（Redis 连接、Playwright 响应处理等）。

::: spiders.base_spider.BaseSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true

## NSFC 爬虫

### NSFCSpiders

国自然爬虫基类，提供公共解析方法。

::: spiders.nsfc.information.nsfc.NSFCSpiders
    handler: python
    options:
      show_root_heading: true
      show_source: true

### ProjectGuideSpiders

项目指南爬虫，用于抓取项目指南信息。

::: spiders.nsfc.information.nsfc_spiders.project_guide.ProjectGuideSpiders
    handler: python
    options:
      show_root_heading: true
      show_source: true

### InstitutionSpiders

机构爬虫，用于抓取机构信息。

::: spiders.nsfc.information.nsfc_spiders.institution.InstitutionSpiders
    handler: python
    options:
      show_root_heading: true
      show_source: true

### GuideNoticeSpiders

指南通知爬虫，用于抓取指南通知信息。

::: spiders.nsfc.information.nsfc_spiders.guide_notice.GuideNoticeSpiders
    handler: python
    options:
      show_root_heading: true
      show_source: true

## RCSB PDB 爬虫

### PDBCompletePlusSpider

RCSB PDB 完整爬虫（优化版），基于 API 获取蛋白质数据库信息。

::: spiders.rcsb_pdb.rcsb_spider_plus.PDBCompletePlusSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true

## 中文文献爬虫

### 万方爬虫

万方数据库爬虫。

::: spiders.chs_article.wanfang_spider.WanfangSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true

## 英文期刊爬虫

### Scopus 爬虫

Scopus 数据库爬虫。

::: spiders.eng_journal.Scopus_spider.ScopusSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true

### Scimagojr 爬虫

Scimagojr 期刊排名爬虫。

::: spiders.eng_journal.Scimagojr_spider.ScimagojrSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true

### LetPub 爬虫

LetPub 期刊查询爬虫。

::: spiders.eng_journal.letpub_spider.LetPubSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true

### Clarivate 爬虫

Clarivate（科睿唯安）期刊爬虫。

::: spiders.eng_journal.clarivate_apider.ClarivateSpider
    handler: python
    options:
      show_root_heading: true
      show_source: true

