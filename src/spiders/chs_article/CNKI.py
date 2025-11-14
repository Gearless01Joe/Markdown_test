# # -*- coding: utf-8 -*-
#
# """
# # @Time    : 2025/8/4 18:30
# # @User  : LGZ
# # @Description  : CNKI爬虫（Scrapy版本）
# """
# from functools import partial
#
# import scrapy
# import re
# import json
# import time
# import traceback
# import asyncio
# from urllib.parse import urljoin
# from typing import cast, Iterable
# from scrapy.http import Request, Response
# from scrapy_playwright.page import PageMethod
# from scrapy.selector import Selector
# import datetime
# from src.component.base_selector_component import BaseSelectorComponent
# from src.spiders.base_spider import BaseSpider
# from playwright.async_api import Page
# from src.component.playwright_helper import PlaywrightTools
# from src.utils.base_logger import BaseLog
# from playwright.async_api import TimeoutError as PlaywrightTimeoutError
#
# custom_logger = BaseLog()
#
#
# class CNKISpider(BaseSpider):
#     name = 'cnki'
#     allowed_domains = ["cnki.net", "kns.cnki.net", "navi.cnki.net"]
#     base_url = "https://navi.cnki.net"
#     years_to_crawl = 5  # 爬取最近几年的数据
#     click_timeout = 5000  # 点击等待延迟
#     network_timeout = 30000  # 等待页面延迟
#     submission_link = "https://xztg.cnki.net/#/complete-journal-collection/selection-detail?id={journal_id}"
#
#     """
#     自定义配置
#     """
#     custom_settings = {
#         "CONCURRENT_REQUESTS": 4,  # 降低并发量
#         "DOWNLOAD_HANDLERS": {
#             "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#             "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#         },
#         "DEFAULT_REQUEST_HEADERS": {
#             'Referer': 'https://navi.cnki.net/knavi/journals/index',
#             'Origin': 'https://navi.cnki.net',
#         },
#         "PLAYWRIGHT_LAUNCH_OPTIONS": {
#             "headless": False,
#         },
#         "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120 * 1000,  # Playwright 请求页面时使用的超时时间
#         # # 每个上下文最大只能打开一个页面，控制瞬时网速
#         # "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 1,
#         # "PLAYWRIGHT_BROWSER_TYPE": "firefox",
#         # "CAPTCHA_URLS": ["kns.cnki.net/verify"],
#         # "CAPTCHA_TRIGGER_PATTERNS": ["知网节超时验证"],
#     }
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         # 爬取最近几年的数据
#         self.years_to_crawl = 5
#         # 已爬取的期刊和年份
#         self.crawled_journals = {}
#         # 信号量控制
#         self.journal_detail_semaphore = asyncio.Semaphore(1)  # 期刊详情页并发数
#         self.journal_submission_semaphore = asyncio.Semaphore(1)  # 期刊投稿页并发数
#         self.paper_semaphore = asyncio.Semaphore(1)  # 文献页并发数，适当提高并发
#
#     def start_requests(self):
#         """
#         开始请求
#         """
#         yield scrapy.Request(
#             "https://navi.cnki.net/knavi/journals/index",
#             callback=self.parse_journal_page,
#             meta={
#                 'playwright': True,
#                 "playwright_include_page": True,
#                 "playwright_page_init_callback": self.init_page,
#                 "playwright_page_methods": [
#                     PageMethod("wait_for_load_state", timeout=self.network_timeout, state="networkidle"),
#                 ],
#             },
#         )
#
#     @staticmethod
#     async def init_page(page, request: Request):
#         """
#         页面初始化
#         """
#         await page.set_extra_http_headers({'Origin': 'https://navi.cnki.net'})
#
#     async def parse_journal_page(self, response: Response, **kwargs):
#         """
#         解析期刊页面
#         """
#         page: Page = response.meta["playwright_page"]
#
#         # 点击"卓越期刊导航"
#         excellent_journal_nav = page.locator('.item:has-text("卓越期刊导航")')
#         await excellent_journal_nav.click(timeout=self.click_timeout)
#
#         # 点击"中国科技期刊卓越行动计划入选项目"
#         excellent_project_link = page.locator('a:has-text("中国科技期刊卓越行动计划入选项目")')
#         await excellent_project_link.click(timeout=self.click_timeout)
#
#         # 循环处理分页
#         while True:
#             # 解析当前页面的期刊列表
#             journal_links = await page.locator('.result a[target="_blank"]').all()
#             for journal_link in journal_links:
#                 # 获取期刊详情页链接
#                 journal_url = await journal_link.get_attribute('href')
#                 if journal_url:
#                     # 等待信号量
#                     await self.journal_detail_semaphore.acquire()
#                     # 提取<h1>标签中的期刊名称
#                     try:
#                         journal_name_element = journal_link.locator('h1')
#                         journal_name = await journal_name_element.inner_text()
#                     except Exception:
#                         journal_name = await journal_link.inner_text()
#                     custom_logger.info(f"开始爬取期刊: {journal_name}")
#
#                     # 完整处理一个期刊的所有数据
#                     yield scrapy.Request(
#                         journal_url,
#                         callback=self.parse_journal_detail,
#                         meta={
#                             'playwright': True,
#                             "playwright_include_page": True,
#                             "playwright_page_init_callback": self.init_page,
#                             "journal_name": journal_name,
#                         },
#                         errback=partial(self.playwright_timeout_error, ctl_semaphore=self.journal_detail_semaphore)
#                     )
#
#             # 检查是否有下一页
#             next_page_button = page.locator('.pagenav .next')
#             if not await next_page_button.is_enabled():
#                 # 不存在下一页
#                 break
#             await next_page_button.click(timeout=self.click_timeout)
#
#     async def parse_journal_detail(self, response: Response, **kwargs):
#         """
#         解析期刊详情页，并直接处理文献列表
#         """
#         page: Page = response.meta["playwright_page"]
#         journal_name = response.meta["journal_name"]
#
#         try:
#             # 提取期刊基本信息
#             selector_model = BaseSelectorComponent()
#
#             # 是否为完全OA期刊
#             selector_model.add_field(
#                 selector="span:has(b.comOA)",
#                 field_name="open_access",
#                 selector_type="css"
#             )
#
#             # 收录信息
#             selector_model.add_field(
#                 selector=".journalType2 label",
#                 field_name="index_list",
#                 selector_type="css",
#                 field_type="list"
#             )
#             # 提取专辑名称
#             selector_model.add_field(
#                 selector="#jiName",
#                 field_name="album_name",
#                 selector_type="css"
#             )
#             # 期刊ID
#             selector_model.add_field(
#                 selector='//input[@id="pykm"]/@value',
#                 field_name="journal_id",
#                 required=True  # 必填
#             )
#
#             extract_result = selector_model.execute_non_yield(response=response)
#             if not extract_result["result"]:
#                 raise ValueError(extract_result["msg"])
#             extract_result = extract_result["data"]
#
#             # 发送投稿页请求
#             yield scrapy.Request(
#                 self.submission_link.format(journal_id=extract_result["journal_id"]),
#                 callback=self.parse_submission_page,
#                 meta={
#                     'playwright': True,
#                     "playwright_page_init_callback": self.init_page,
#                     "journal_info": extract_result
#                 },
#                 errback=partial(self.playwright_timeout_error, ctl_semaphore=None)
#             )
#
#             # 输出收集到的期刊详情和投稿页数据
#             custom_logger.info(f"已爬取期刊: {journal_name} 的详情和投稿数据")
#             custom_logger.info(f"期刊数据: {extract_result}")
#
#             # 处理文献列表数据
#             custom_logger.info(f"开始爬取期刊: {journal_name} 的文献数据")
#
#             # 在原页面上处理文献列表
#             await page.wait_for_timeout(3000)
#             await PlaywrightTools.page_screen_scroll(page=page, scroll_type="bottom")
#
#             # 获取当前年份并计算爬取范围
#             current_year = datetime.datetime.now().year
#             start_year = current_year - self.years_to_crawl + 1
#
#             # 获取所有年份区域
#             year_areas = await page.query_selector_all('.yearissuepage')
#             if not year_areas:
#                 custom_logger.warning(f"未找到期刊 {journal_name} 的年份导航区域")
#                 return
#
#             # 收集年份信息
#             all_years = []
#             for year_area in year_areas:
#                 dl_elements = await year_area.query_selector_all('dl')
#                 for dl in dl_elements:
#                     dl_id = await dl.get_attribute('id')
#                     dl_class = await dl.get_attribute('class')
#
#                     if not dl_id or not 'Year_Issue' in dl_id:
#                         continue
#
#                     try:
#                         year_match = re.search(r'(\d{4})_Year_Issue', dl_id)
#                         if year_match:
#                             year_number = int(year_match.group(1))
#                             if year_number >= start_year:
#                                 all_years.append({
#                                     'year_number': year_number,
#                                     'dl_element': dl,
#                                     'dl_id': dl_id,
#                                     'is_current': 'cur' in dl_class if dl_class else False
#                                 })
#                     except Exception as e:
#                         custom_logger.warning(f"解析年份ID {dl_id} 时出错: {e}")
#
#             # 按年份降序排列（从最新到最旧）
#             all_years.sort(key=lambda x: x['year_number'], reverse=True)
#             custom_logger.info(f"将处理期刊 {journal_name} 的年份: {[y['year_number'] for y in all_years]}")
#
#             # 逐个处理年份
#             for year_info in all_years:
#                 year_number = year_info['year_number']
#                 dl_element = year_info['dl_element']
#                 is_current = year_info['is_current']
#
#                 custom_logger.info(f"处理期刊 {journal_name} 的年份: {year_number}")
#
#                 try:
#                     # 确保年份元素可见
#                     await dl_element.evaluate("(element) => element.scrollIntoView({block: 'center'})")
#                     await page.wait_for_timeout(1000)
#
#                     # 获取年份的dt元素
#                     year_dt = await dl_element.query_selector('dt')
#
#                     # 如果年份未展开，点击展开
#                     if not is_current:
#                         custom_logger.info(f"年份 {year_number} 未展开，点击展开")
#                         await year_dt.click()
#                         await page.wait_for_timeout(2000)
#
#                     # 获取该年份下的所有期号
#                     dd_element = await dl_element.query_selector('dd')
#                     if dd_element:
#                         issue_links = await dd_element.query_selector_all('a')
#
#                         if not issue_links:
#                             custom_logger.warning(f"期刊 {journal_name} 年份 {year_number} 未找到期号")
#                             continue
#
#                         custom_logger.info(f"期刊 {journal_name} 年份 {year_number} 找到 {len(issue_links)} 个期号")
#
#                         # 按照期号ID排序，确保从最新期号开始处理
#                         issues_data = []
#                         for issue_link in issue_links:
#                             issue_id = await issue_link.get_attribute('id')
#                             issue_text = await issue_link.text_content()
#                             issue_value = await issue_link.get_attribute('value')
#
#                             # 提取期号编号进行排序
#                             issue_number_match = re.search(r'No\.(\d+)', issue_text)
#                             issue_number = int(issue_number_match.group(1)) if issue_number_match else 0
#
#                             issues_data.append({
#                                 'issue_id': issue_id,
#                                 'issue_text': issue_text,
#                                 'issue_value': issue_value,
#                                 'issue_number': issue_number,
#                                 'issue_link': issue_link
#                             })
#
#                         # 按期号降序排列（从最新到最旧）
#                         issues_data.sort(key=lambda x: x['issue_number'], reverse=True)
#
#                         # 逐个处理期号
#                         for issue_data in issues_data:
#                             issue_id = issue_data['issue_id']
#                             issue_text = issue_data['issue_text']
#                             issue_link = issue_data['issue_link']
#
#                             custom_logger.info(f"处理期刊 {journal_name} 年份 {year_number} 期号: {issue_text}")
#
#                             # 点击期号链接
#                             await issue_link.click()
#                             await page.wait_for_timeout(3000)
#
#                             # 等待文献列表加载
#                             try:
#                                 await page.wait_for_selector('#CataLogContent', timeout=10000)
#
#                                 # 查找文献列表
#                                 literature_items = await page.query_selector_all('#CataLogContent dd.row')
#
#                                 if not literature_items:
#                                     custom_logger.warning(
#                                         f"期刊 {journal_name} 年份 {year_number} 期号 {issue_text} 未找到文献")
#                                     continue
#
#                                 custom_logger.info(
#                                     f"期刊 {journal_name} 年份 {year_number} 期号 {issue_text} 找到 {len(literature_items)} 篇文献")
#
#                                 # 处理每篇文献
#                                 for item in literature_items:
#                                     # 获取文献标题链接
#                                     title_link = await item.query_selector('.name a')
#                                     if not title_link:
#                                         # 尝试其他可能的选择器
#                                         title_link = await item.query_selector('a')
#
#                                     if title_link:
#                                         title_text = await title_link.text_content()
#                                         literature_url = await title_link.get_attribute('href')
#
#                                         if literature_url:
#                                             custom_logger.info(f"发送文献请求: {title_text}")
#
#                                             # 获取页码信息
#                                             page_elem = await item.query_selector('.company')
#                                             page_info = await page_elem.text_content() if page_elem else ""
#                                             await self.paper_semaphore.acquire()
#                                             # 直接发送请求
#                                             yield scrapy.Request(
#                                                 literature_url,
#                                                 callback=self.parse_literature,
#                                                 meta={
#                                                     'playwright': True,
#                                                     "playwright_include_page": True,
#                                                     "playwright_page_init_callback": self.init_page,
#                                                     "journal_name": journal_name,
#                                                     "issue_info": f"{year_number}-{issue_text}",
#                                                     "title_text": title_text,
#                                                     "page_info": page_info,
#                                                 },
#                                                 errback=partial(self.playwright_timeout_error, ctl_semaphore=self.paper_semaphore)
#                                             )
#                             except Exception as e:
#                                 custom_logger.error(f"处理期号 {issue_text} 的文献时出错: {e}")
#                                 traceback.print_exc()
#                     else:
#                         custom_logger.warning(f"期刊 {journal_name} 年份 {year_number} 未找到期号容器")
#
#                 except Exception as e:
#                     custom_logger.error(f"处理年份 {year_number} 时出错: {e}")
#                     traceback.print_exc()
#
#         finally:
#             # 所有文献请求都已发送，可以安全地关闭页面和释放信号量
#             custom_logger.info(f"期刊 {journal_name} 的所有文献请求已发送，关闭页面")
#             await page.close()
#             self.journal_detail_semaphore.release()
#
#
#     async def parse_literature(self, response: Response, **kwargs):
#         """
#         解析文献详情页
#         """
#         page = response.meta.get("playwright_page")
#         journal_name = response.meta.get("journal_name")
#         issue_info = response.meta.get("issue_info")
#         title_text = response.meta.get("title_text")
#         author = response.meta.get("author")
#         page_info = response.meta.get("page_info")
#
#         try:
#             literature_data = {}
#
#             # 添加来源信息
#             literature_data['journal_name'] = journal_name
#             literature_data['issue_info'] = issue_info
#             literature_data['title'] = title_text
#             literature_data['author'] = author
#             literature_data['page_info'] = page_info
#
#             # 提取作者和机构信息
#             author_result = self._parse_author_institutions(response)
#             literature_data["authors"] = author_result["authors"]
#             literature_data["institutions"] = author_result["institutions"]
#
#             # 提取摘要
#             abstract_element = await page.query_selector('#ChDivSummary')
#             if abstract_element:
#                 literature_data['abstract'] = await abstract_element.text_content()
#
#             # 提取关键词
#             keywords_data = []
#             keyword_elements = await page.query_selector_all('.keywords a')
#             for keyword_element in keyword_elements:
#                 keyword = await keyword_element.text_content()
#                 keywords_data.append(keyword.strip().rstrip(';'))
#             literature_data['keywords'] = keywords_data
#
#             # 提取基金资助
#             fund_elements = await page.query_selector_all('.funds a')
#             funds = []
#             for fund_element in fund_elements:
#                 fund = await fund_element.text_content()
#                 funds.append(fund.strip().rstrip('；'))
#             literature_data['funds'] = funds
#
#             # 提取分类信息
#             category_elements = await page.query_selector_all('li .rowtit:has-text("分类号：") + p')
#             if category_elements:
#                 clc_codes = await category_elements[0].text_content()
#                 literature_data['clc_code'] = clc_codes
#
#             # 提取页码
#             page_info_element = await page.query_selector('.total-inform span:has-text("页码")')
#             if page_info_element:
#                 page_info = await page_info_element.text_content()
#                 page_numbers = page_info.replace('页码：', '').strip()
#                 literature_data['page_numbers'] = page_numbers
#
#             # 滚动页面到底部
#             await PlaywrightTools.page_screen_scroll(page=page, scroll_type="bottom")
#
#             # 提取参考文献
#             references = []
#             reference_sections = await page.query_selector_all(
#                 '#div-literatureRef > div[id^="nxgp-kcms-data-ref-references-"]')
#
#             for section in reference_sections:
#                 ref_type = await section.get_attribute('type')
#
#                 reference_items = await section.query_selector_all('ul.ebBd li')
#                 for ref_item in reference_items:
#                     ref_text = await ref_item.text_content()
#                     ref_text = re.sub(r'^\\[\\d+\\]\s*', '', ref_text.strip())
#                     references.append({
#                         'type': ref_type,
#                         'reference': ref_text
#                     })
#
#                 # 处理参考文献分页
#                 has_next_page = await section.evaluate("""
#                     (element) => {
#                         const pageContainer = element.querySelector('.page_journal');
#                         if (!pageContainer) return false;
#
#                         const nextButton = pageContainer.querySelector('.next');
#                         return nextButton != null && !nextButton.classList.contains('disabled');
#                     }
#                 """)
#
#                 page_num = 1
#                 while has_next_page:
#                     page_num += 1
#                     try:
#                         next_button = await section.query_selector('.page_journal .next')
#                         if not next_button or await next_button.is_disabled():
#                             break
#
#                         await next_button.click()
#                         await page.wait_for_timeout(2000)
#
#                         # 处理可能出现的验证码
#                         try:
#                             captcha_present = await page.is_visible('.canvas_wrap', timeout=3000)
#                             if captcha_present:
#                                 await self.handle_popup_captcha_if_present(page)
#                         except:
#                             pass
#
#                         more_reference_items = await section.query_selector_all('ul.ebBd li')
#                         for ref_item in more_reference_items:
#                             ref_text = await ref_item.text_content()
#                             ref_text = re.sub(r'^\\[\\d+\\]\s*', '', ref_text.strip())
#                             references.append({
#                                 'type': ref_type,
#                                 'reference': ref_text
#                             })
#
#                         has_next_page = await section.evaluate("""
#                             (element) => {
#                                 const pageContainer = element.querySelector('.page_journal');
#                                 if (!pageContainer) return false;
#
#                                 const nextButton = pageContainer.querySelector('.next');
#                                 return nextButton != null && !nextButton.classList.contains('disabled');
#                             }
#                         """)
#                     except Exception as e:
#                         custom_logger.error(f"处理参考文献第 {page_num} 页时出错: {e}")
#                         break
#
#             literature_data['references'] = references
#
#             custom_logger.info(f"文献 '{title_text}' 数据提取完成，共 {len(references)} 条参考文献")
#
#             return literature_data
#
#         except Exception as e:
#             custom_logger.error(f"处理文献 '{title_text}' 详情时出错: {e}")
#             traceback.print_exc()
#             return None
#         finally:
#             # 确保释放页面和信号量
#             if page:
#                 await page.close()
#             # 释放信号量
#             self.paper_semaphore.release()
#             custom_logger.info(f"文献 '{title_text}' 的信号量已释放")
#
#     def parse_submission_page(self, response: Response, **kwargs):
#         """
#         解析投稿链接信息
#         :param response:
#         :param kwargs:
#         :return:
#         """
#         # 处理表格数据
#         table_mapping = {}
#         table_selector = response.css('tr.ant-descriptions-row')
#         table_selector = cast(Iterable[Selector], table_selector)  # 显式声明类型
#         for row in table_selector:
#             # 获取当前行中的所有<th>和<td>元素
#             cells = row.css('th.ant-descriptions-item-label, td.ant-descriptions-item-content')
#
#             # 成对处理标签和内容
#             for i in range(0, len(cells), 2):
#                 if i + 1 >= len(cells):
#                     break
#
#                 # 获取标签名和对应的值
#                 label = cells[i].css('::text').get().strip('：').strip()
#                 value = cells[i + 1].css('::text').get().strip()
#
#                 # 将键值对存入字典
#                 if label and value and value != "暂无":
#                     table_mapping[label] = value
#
#         # 过滤掉不需要的数据
#         filtered_mapping = {k: v for k, v in table_mapping.items() if k not in [
#             '邮发代号', '开本', '出版文献量', '总下载次数', '专题名称', '基金文献量', '总被引次数'
#         ]}
#
#         # 执行提取
#         selector_model = BaseSelectorComponent()
#         # 封面图
#         selector_model.add_field(
#             selector=".show-img img::attr(src)",
#             field_name="cover_image",
#             selector_type="css",
#             field_type="text"
#         )
#         # 期刊中文名
#         selector_model.add_field(
#             selector=".basics-info-left h2 a::text",
#             field_name="title",
#             selector_type="css",
#             field_type="text"
#         )
#         # 期刊英文名
#         selector_model.add_field(
#             selector=".Eng-title:not(.former-title)::text",
#             field_name="eng_title",
#             selector_type="css",
#             field_type="text"
#         )
#         # 曾用刊名
#         selector_model.add_field(
#             selector=".Eng-title.former-title::text",
#             field_name="former_title",
#             selector_type="css",
#             field_type="text"
#         )
#         # 出版周期
#         selector_model.add_field(
#             selector='.stat-item:contains("出版周期") p::text',
#             field_name="publish_cycle",
#             selector_type="css",
#             field_type="text"
#         )
#         # 期刊介绍 (获取所有段落)
#         selector_model.add_field(
#             selector='.desc-text p::text',
#             field_name="description_paragraphs",
#             selector_type="css",
#             field_type="list"
#         )
#         # 执行提取
#         extract_result = selector_model.execute_non_yield(response=response)
#         if not extract_result["result"]:
#             raise ValueError(extract_result["msg"])
#         extract_data = extract_result["data"]
#
#         # 处理曾用刊名，移除"曾用刊名："前缀
#         if "former_title" in extract_data and extract_data["former_title"]:
#             extract_data["former_title"] = extract_data["former_title"].replace('曾用刊名：', '').strip()
#
#         # 合并表格数据与提取数据
#         result_data = {**filtered_mapping, **extract_data}
#
#         # 处理期刊介绍段落，合并为一个字符串
#         if "description_paragraphs" in result_data and result_data["description_paragraphs"]:
#             paragraphs = [p.strip() for p in result_data["description_paragraphs"] if p and p.strip()]
#             if paragraphs:
#                 result_data["description"] = '\n'.join(paragraphs)
#             del result_data["description_paragraphs"]
#
#         # 添加停刊判断逻辑
#         if '收录结束年' in result_data:
#             try:
#                 import datetime
#                 current_year = datetime.datetime.now().year
#                 end_year = int(result_data['收录结束年'])
#
#                 if end_year < current_year:
#                     result_data['is_discontinued'] = 1
#                 else:
#                     result_data['is_discontinued'] = 0
#             except Exception as e:
#                 self.logger.error(f"判断是否停刊时出错: {e}")
#
#         # 统一字段命名
#         field_mapping = {
#             '主管单位': 'supervisor',
#             '主办单位': 'sponsor',
#             'ISSN': 'issn',
#             'CN': 'cn',
#             '创刊时间': 'founded_year',
#             '出版地': 'publication_place',
#             '语种': 'language',
#             '收录结束年': 'end_year',
#             '主编': 'editor',
#             '副主编': 'deputy_editor',
#             '网址': 'website',
#             'E-mail': 'email',
#             '电话': 'phone',
#         }
#
#         # 重命名字段
#         renamed_data = {}
#         for key, value in result_data.items():
#             if key in field_mapping:
#                 renamed_data[field_mapping[key]] = value
#             else:
#                 renamed_data[key] = value
#
#         custom_logger.debug(f"投稿数据:{renamed_data}")
#
#
#
#
#     # async def parse_literature_detail(self, response: Response, **kwargs):
#     #     """
#     #     解析文献详情页
#     #     """
#     #     page = response.meta.get("playwright_page")
#     #     journal_name = response.meta.get("journal_name")
#     #     issue_info = response.meta.get("issue_info")
#     #     title_text = response.meta.get("title_text")
#     #     paper_semaphore = response.meta.get("paper_semaphore")
#     #
#     #     # 在处理文献详情前获取信号量
#     #     await paper_semaphore.acquire()
#     #     custom_logger.info(f"已为文献 '{title_text}' 获取信号量")
#     #
#     #     try:
#     #         custom_logger.info(f"开始处理文献详情: {title_text}")
#     #         literature_data = {}
#     #
#     #         # 添加来源信息
#     #         literature_data['journal_name'] = journal_name
#     #         literature_data['issue_info'] = issue_info
#     #         literature_data['title'] = title_text
#     #
#     #         # 提取作者和机构信息
#     #         author_result = self._parse_author_institutions(response)
#     #         literature_data["authors"] = author_result["authors"]
#     #         literature_data["institutions"] = author_result["institutions"]
#     #
#     #         # 提取摘要
#     #         abstract_element = await page.query_selector('#ChDivSummary')
#     #         if abstract_element:
#     #             literature_data['abstract'] = await abstract_element.text_content()
#     #
#     #         # 提取关键词
#     #         keywords_data = []
#     #         keyword_elements = await page.query_selector_all('.keywords a')
#     #         for keyword_element in keyword_elements:
#     #             keyword = await keyword_element.text_content()
#     #             keywords_data.append(keyword.strip().rstrip(';'))
#     #         literature_data['keywords'] = keywords_data
#     #
#     #         # 提取基金资助
#     #         fund_elements = await page.query_selector_all('.funds a')
#     #         funds = []
#     #         for fund_element in fund_elements:
#     #             fund = await fund_element.text_content()
#     #             funds.append(fund.strip().rstrip('；'))
#     #         literature_data['funds'] = funds
#     #
#     #         # 提取分类信息
#     #         category_elements = await page.query_selector_all('li .rowtit:has-text("分类号：") + p')
#     #         if category_elements:
#     #             clc_codes = await category_elements[0].text_content()
#     #             literature_data['clc_code'] = clc_codes
#     #
#     #         # 提取页码
#     #         page_info_element = await page.query_selector('.total-inform span:has-text("页码")')
#     #         if page_info_element:
#     #             page_info = await page_info_element.text_content()
#     #             page_numbers = page_info.replace('页码：', '').strip()
#     #             literature_data['page_numbers'] = page_numbers
#     #
#     #         # 滚动页面到底部获取参考文献
#     #         await PlaywrightTools.page_screen_scroll(page=page, scroll_type="bottom")
#     #
#     #         # 提取参考文献
#     #         references = []
#     #         reference_sections = await page.query_selector_all(
#     #             '#div-literatureRef > div[id^="nxgp-kcms-data-ref-references-"]')
#     #         for section in reference_sections:
#     #             # 获取参考文献类型
#     #             ref_type = await section.get_attribute('type')
#     #
#     #             # 获取该类型下的所有参考文献
#     #             reference_items = await section.query_selector_all('ul.ebBd li')
#     #             for ref_item in reference_items:
#     #                 ref_text = await ref_item.text_content()
#     #                 # 移除前面的编号
#     #                 ref_text = re.sub(r'^\\[\\d+\\]\s*', '', ref_text.strip())
#     #                 references.append({
#     #                     'type': ref_type,
#     #                     'reference': ref_text
#     #                 })
#     #
#     #             # 处理参考文献分页
#     #             has_next_page = await section.evaluate("""
#     #                 (element) => {
#     #                     const pageContainer = element.querySelector('.page_journal');
#     #                     if (!pageContainer) return false;
#     #
#     #                     const nextButton = pageContainer.querySelector('.next');
#     #                     return nextButton != null && !nextButton.classList.contains('disabled');
#     #                 }
#     #             """)
#     #
#     #             page_num = 1
#     #             while has_next_page:
#     #                 page_num += 1
#     #                 try:
#     #                     # 点击下一页按钮
#     #                     next_button = await section.query_selector('.page_journal .next')
#     #                     if not next_button or await next_button.is_disabled():
#     #                         break
#     #
#     #                     await next_button.click()
#     #                     await page.wait_for_timeout(2000)
#     #
#     #                     # 处理可能出现的验证码
#     #                     try:
#     #                         captcha_present = await page.is_visible('.canvas_wrap', timeout=3000)
#     #                         if captcha_present:
#     #                             await self.handle_popup_captcha_if_present(page)
#     #                     except:
#     #                         pass
#     #
#     #                     # 获取下一页的参考文献
#     #                     more_reference_items = await section.query_selector_all('ul.ebBd li')
#     #                     for ref_item in more_reference_items:
#     #                         ref_text = await ref_item.text_content()
#     #                         # 移除前面的编号
#     #                         ref_text = re.sub(r'^\\[\\d+\\]\s*', '', ref_text.strip())
#     #                         references.append({
#     #                             'type': ref_type,
#     #                             'reference': ref_text
#     #                         })
#     #
#     #                     # 检查是否还有下一页
#     #                     has_next_page = await section.evaluate("""
#     #                         (element) => {
#     #                             const pageContainer = element.querySelector('.page_journal');
#     #                             if (!pageContainer) return false;
#     #
#     #                             const nextButton = pageContainer.querySelector('.next');
#     #                             return nextButton != null && !nextButton.classList.contains('disabled');
#     #                         }
#     #                     """)
#     #                 except Exception as e:
#     #                     custom_logger.error(f"处理参考文献第 {page_num} 页时出错: {e}")
#     #                     break
#     #
#     #         literature_data['references'] = references
#     #
#     #         custom_logger.info(f"文献 '{title_text}' 数据提取完成，共 {len(references)} 条参考文献")
#     #
#     #         # 返回提取的数据
#     #         return literature_data
#     #
#     #     except Exception as e:
#     #         custom_logger.error(f"处理文献 '{title_text}' 详情时出错: {e}")
#     #         traceback.print_exc()
#     #         return None
#     #     finally:
#     #         # 确保释放页面和信号量
#     #         if page:
#     #             await page.close()
#     #         # 必须在finally中释放信号量，确保不会导致死锁
#     #         if paper_semaphore:
#     #             paper_semaphore.release()
#     #             custom_logger.info(f"文献 '{title_text}' 的信号量已释放")
#
#
#     @staticmethod
#     def _parse_author_institutions(response: Response):
#         """
#         解析作者机构信息
#         :author Mabin
#         :param response:
#         :return:
#         """
#         # 提取作者信息
#         authors = []
#         author_spans = response.xpath('//h3[@class="author" and @id="authorpart"]/span')
#         author_spans = cast(Iterable[Selector], author_spans)  # 显式声明类型
#         for span in author_spans:
#             name = span.xpath('.//a/text()').get()
#             if name:
#                 # 提取作者名和编号（如"蔡云帆1"中的1）
#                 name = name.strip()
#                 sup = span.xpath('.//sup/text()').get()
#                 author_code = span.xpath('.//input[@class="authorcode"]/@value').get()
#                 email = span.xpath('.//p[@class="authortip"]/text()').get()
#
#                 authors.append({
#                     'name': name.replace(sup, '') if sup else name,
#                     'number': int(sup) if sup else None,
#                     'author_code': author_code,
#                     'email': email.strip() if email else None
#                 })
#
#         # 提取机构信息
#         institutions = []
#         institution_spans = response.xpath('//h3[@class="author" and not(@id)]/span')
#         institution_spans = cast(Iterable[Selector], institution_spans)  # 显式声明类型
#         for span in institution_spans:
#             institution = span.xpath('.//a/text()').get()
#             if institution:
#                 # 提取机构名和编号（如"1.天津大学..."中的1）
#                 institution = institution.strip()
#                 number = institution.split('.')[0] if '.' in institution else None
#
#                 institutions.append({
#                     'number': int(number) if number else None,
#                     'name': '.'.join(institution.split('.')[1:]).strip() if '.' in institution else institution
#                 })
#
#         # 建立作者与机构的对应关系
#         for author in authors:
#             if author['number']:
#                 # 根据作者的编号找到对应的机构
#                 matching_institutions = [inst for inst in institutions if inst['number'] == author['number']]
#                 author['institution'] = matching_institutions[0]['name'] if matching_institutions else None
#
#         return {
#             'authors': authors,
#             'institutions': institutions
#         }
#
#     async def handle_popup_captcha_if_present(self, page: Page):
#         """
#         处理弹窗验证码
#         """
#         try:
#             # 等待验证码出现，设置较短的超时时间
#             is_visible = await page.is_visible('.canvas_wrap', timeout=5000)
#
#             if is_visible:
#                 custom_logger.info("检测到弹窗验证码，正在处理...")
#
#                 # 使用PlaywrightTools处理滑块验证码
#                 slide_result = await PlaywrightTools.slide_verify(
#                     page=page,
#                     slider_selector=".canvas_slider",
#                     bg_canvas_selector=".canvas_wrap canvas:nth-child(1)",
#                     gap_canvas_selector=".canvas_wrap canvas:nth-child(2)",
#                 )
#
#                 if not slide_result["result"]:
#                     custom_logger.warning(f"弹窗验证码处理失败: {slide_result['msg']}")
#                 else:
#                     custom_logger.info("弹窗验证码处理完成")
#                     # 等待验证结果
#                     await page.wait_for_timeout(2000)
#         except Exception as e:
#             custom_logger.error(f"处理弹窗验证码时出错: {e}")
#
#     async def playwright_timeout_error(self, failure, ctl_semaphore: asyncio.Semaphore = None):
#         """
#         Playwright超时重试回调
#         :author Mabin
#         :param failure:
#         :param ctl_semaphore:信号量
#         :return:
#         """
#         self.logger.error(f"Request failed: {failure}")
#
#         # 获取最大重试次数
#         retry_times = self.crawler.settings.getint('RETRY_TIMES', 3)
#
#         # 获取请求信息
#         request = failure.request
#         if request.meta.get('retry_times', 0) < retry_times:
#             # 复制请求，重新发送
#             retryreq = request.copy()
#             retryreq.meta['retry_times'] = request.meta.get('retry_times', 0) + 1
#
#             return retryreq
#         else:
#             # 超过最大重试次数，则释放信号量
#             if ctl_semaphore:
#                 ctl_semaphore.release()