# -*- coding: utf-8 -*-

"""
# @Time    : 2025/9/2 9:22
# @User  : Mabin
# @Description  :
"""
import re
import html
import scrapy
from scrapy.selector import Selector
from collections import defaultdict
from scrapy.http import Request, Response
from src.spiders.base_spider import BaseSpider
from src.component.base_selector_component import BaseSelectorComponent
from src.utils.utils import en_cn_correction
from src.items.other.eng_journal_item import EngJournalItem, JOURNAL_OPEN_ACCESS
# from src.items.other.detail_fields_item import DetailFieldsItem


class LetPubSpider(BaseSpider):
    name = 'letpub_journal'
    allowed_domains = ["www.letpub.com.cn", "aliyuncs.com"]
    base_url = "https://www.letpub.com.cn"

    # 默认GET请求
    start_urls = [
        'https://www.letpub.com.cn/index.php?page=journalapp&view=researchfield&fieldtag=&firstletter='
    ]

    """
    自定义配置
    """
    custom_settings = {
        'ITEM_PIPELINES': {
            # 'src.pipelines.storage.detail_fields_pipeline.DetailFieldsPipeline': 301,
            'src.pipelines.file_download_pipeline.FileDownloadPipeline': 100,
            'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 200,
            'src.pipelines.storage.eng_journal_pipeline.EngJournalPipeline': 301,
        },
        "CONCURRENT_REQUESTS_PER_IP": 3,  # 单个IP执行的最大并发（即同时）请求数
    }

    def parse(self, response, **kwargs):
        """
        解析LetPub列表页
        :author:Mabin
        :param response:
        :param kwargs:
        :return:
        """
        if "您请求页面的速度过快" in response.text:
            # 重发请求
            retry_request = response.request
            retry_request.dont_filter = True
            yield retry_request
            return

        print(response.url)
        # 执行提取
        selector_model = BaseSelectorComponent()

        # 列表信息
        base_name = "journal_list"
        base_selector = "//tr[count(td)=12]"
        selector_model.add_field(  # ISSN
            selector="./td[1]",
            field_name="issn",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 期刊名
            selector="./td[2]/a",
            field_name="journal_name",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 期刊缩写名
            selector="./td[2]/font",
            field_name="abbr_name",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 是否OA
            selector="./td[8]",
            field_name="is_oa",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 录用比例
            selector="./td[9]",
            field_name="hiring_ratio",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 审稿周期
            selector="./td[10]",
            field_name="review_cycle",
            base_name=base_name,
            base_selector=base_selector,
        )
        selector_model.add_field(  # 详情页链接
            selector="./td[2]/a/@href",
            field_name="detail_page",
            field_type="href",
            base_name=base_name,
            base_selector=base_selector,
            callback=self.get_detail_page,
        )
        selector_model.add_field(  # 下一页链接
            selector="(//a[contains(text(),'下一页')])[1]/@href",
            field_name="next_page",
            field_type="href",
            callback=self.parse,
        )

        # 执行提取
        yield from selector_model.execute(response=response)

    def get_detail_page(self, response: Response, **kwargs):
        """
        解析详情页数据
        :author:Mabin
        :param response:
        :param kwargs:
        :return:
        """
        if "您请求页面的速度过快" in response.text:
            # 重发请求
            retry_request = response.request
            retry_request.dont_filter = True
            yield retry_request
            return

        list_info = response.meta

        # 转换表格为字典映射
        filter_sign = True
        table_mapping = defaultdict(list)
        table_trs = response.xpath('//*[@class="table_yjfx"]/tbody/tr')
        for tr_item in table_trs:  # type: ignore
            tds = tr_item.xpath('./td').getall()

            index_name = None
            for i, td_item in enumerate(tds):
                if i == 0:
                    # 首个
                    index_name = BaseSelectorComponent.get_sub_sup_text(td_item)

                    # 修正名称
                    standard_set = {"CiteScore", "APC", "版面费", "JCR分区"}
                    for standard_item in standard_set:
                        if standard_item in index_name:
                            index_name = standard_item
                            break

                    if "中国科学院期刊分区" in index_name and "最新" in index_name:
                        index_name = "中国科学院期刊分区"

                if index_name == "期刊名字":
                    # 从期刊名字之后的数据开始处理
                    filter_sign = False

                if filter_sign or not index_name:
                    # 需要跳过的数据
                    continue

                # 解析相关数据
                current_val = BaseSelectorComponent.get_sub_sup_text(td_item)

                # 规整相关数据
                if current_val in {"N.A.", "-", "N/A"}:
                    current_val = None
                elif "暂无" in current_val:
                    current_val = None

                # 记录节点数据
                table_mapping[index_name].append({
                    "origin": td_item,
                    "parsed": current_val
                })

        # for key, item in table_mapping.items():
        #     yield DetailFieldsItem(
        #         data_key=key,
        #         data_value=item[-1].get("parsed"),
        #         page_url=response.url,
        #     )

        # 提取中科院分区数据
        area_rank = self.extract_chart_data(response)

        # 提取CiteScore
        cite_score = {}
        if table_mapping["CiteScore"]:
            cite_score = self.extract_cite_score(
                origin_html=table_mapping["CiteScore"][-1].get("origin"),
                thead_text=table_mapping["CiteScore"][0].get("parsed"),
            )

        # 提取JCR
        jcr_info = {}
        if table_mapping["JCR分区"]:
            jcr_info = self.extract_jcr_info(
                origin_html=table_mapping["JCR分区"][-1].get("origin"),
                thead_text=table_mapping["JCR分区"][0].get("parsed"),
            )

        # 提取中科院分区
        zky_info = {}
        if table_mapping["中国科学院期刊分区"]:
            zky_info = self.get_zky_info(
                origin_html=table_mapping["中国科学院期刊分区"][-1].get("origin"),
                thead_text=table_mapping["中国科学院期刊分区"][0].get("parsed"),
            )

        # 提取封面图
        analysis_selector = Selector(
            text=html.unescape(table_mapping["期刊名字"][0].get("origin")).strip()  # type: ignore
        )
        cover_image = analysis_selector.xpath("//img/@src").get()

        # 组织入库数据
        buf = {
            "journal_name": list_info.get("journal_name"),  # 期刊名字
            "abbr_name": list_info.get("abbr_name"),  # 缩写名称
            "source_img": cover_image,  # 期刊封面图
            "file_urls": [cover_image],  # 下载文件链接
            "acceptance_ratio": list_info.get("hiring_ratio"),  # 文献录用比例
            "review_cycle": list_info.get("review_cycle"),  # 平均审稿速度
            "issn": list_info.get("issn"),  # 期刊ISSN
            "page_url": response.url,
            "original_html": response.text,
        }
        if table_mapping.get("E-ISSN"):
            buf["eissn"] = table_mapping["E-ISSN"][-1].get("parsed")
        if table_mapping.get("JCI期刊引文指标"):
            buf["jci_citation_index"] = table_mapping["JCI期刊引文指标"][-1].get("parsed")
        if table_mapping.get("h-index"):
            buf["h_index"] = table_mapping["h-index"][-1].get("parsed")
        if table_mapping.get("P-ISSN"):  # P-ISSN
            buf["pissn"] = table_mapping["P-ISSN"][-1].get("parsed")
        if table_mapping.get("期刊简介"):
            buf["scope"] = table_mapping["期刊简介"][-1].get("parsed")
        if table_mapping.get("期刊官方网站"):
            buf["journal_website"] = table_mapping["期刊官方网站"][-1].get("parsed")
        if table_mapping.get("期刊投稿网址"):
            buf["publish_link"] = table_mapping["期刊投稿网址"][-1].get("parsed")
        if table_mapping.get("作者指南网址"):
            buf["author_guide_url"] = table_mapping["作者指南网址"][-1].get("parsed")
        if table_mapping.get("通讯方式"):
            buf["publisher_address"] = table_mapping["通讯方式"][-1].get("parsed")
        if table_mapping.get("出版商"):
            buf["publisher"] = table_mapping["出版商"][-1].get("parsed")
        if table_mapping.get("涉及的研究方向"):
            buf["research_direction"] = table_mapping["涉及的研究方向"][-1].get("parsed")
        if table_mapping.get("出版国家或地区"):
            buf["country"] = table_mapping["出版国家或地区"][-1].get("parsed")
        if table_mapping.get("出版语言"):
            buf["language"] = table_mapping["出版语言"][-1].get("parsed")
        if table_mapping.get("出版周期"):
            buf["publication_cycle"] = table_mapping["出版周期"][-1].get("parsed")
        if table_mapping.get("出版年份") and table_mapping.get("出版年份") != "0":
            buf["year"] = table_mapping["出版年份"][-1].get("parsed")
        # 是否开放获取
        if str(list_info.get("is_oa")).lower() == "yes":
            buf["openaccess"] = JOURNAL_OPEN_ACCESS["open"]
        else:
            buf["openaccess"] = JOURNAL_OPEN_ACCESS["not_open"]

        # SNIP
        if cite_score.get("SNIP"):
            buf["snip"] = cite_score.get("SNIP")
        # CiteScore
        if cite_score.get("CiteScore"):
            buf["citescore"] = cite_score.get("CiteScore")
        # SJR
        if cite_score.get("SJR"):
            buf["sjr"] = cite_score.get("SJR")
        # CiteScore排名
        if cite_score.get("CiteScore排名"):
            buf["citescore_quartiles"] = cite_score.get("CiteScore排名")
        # JIF(即JCR)分区排名
        if jcr_info.get("jif"):
            buf["jcr_quartiles"] = jcr_info.get("jif")
        # JCI分区排名
        if jcr_info.get("jci"):
            buf["jci_quartiles"] = jcr_info.get("jci")
        # 中科院分区
        if zky_info.get("data"):
            buf["cas_quartiles"] = zky_info.get("data")
        # 中国科学院期刊分区-Top期刊
        if zky_info.get("top_journal"):
            buf["top_journal"] = zky_info.get("top_journal")

        # 版面信息
        fee_info = {}
        for fee_item in [table_mapping.get("APC"), table_mapping.get("版面费"), table_mapping.get("OA期刊相关信息")]:
            # 遍历版面费字段，优先级按高从低
            if not fee_item:
                continue

            # 解析相关信息
            tmp_fee = self.parse_journal_info(fee_item[-1].get("origin"))

            # 数据去空
            tmp_fee = {k: v for k, v in tmp_fee.items() if v}
            if not tmp_fee:
                continue

            # 字典合并
            fee_info = {**tmp_fee, **fee_info}
        if fee_info:
            buf["journal_extra_info"] = fee_info

        # 在线出版周期
        if table_mapping.get("在线出版周期"):
            # 解析相关情况
            analysis_selector = Selector(
                text=html.unescape(table_mapping["在线出版周期"][-1].get("origin")).strip()  # type: ignore
            )
            buf["online_publish_cycle"] = analysis_selector.xpath(
                '//b[contains(text(), "来源")]/following-sibling::text()'
            ).get()

        # 编辑信息
        if table_mapping.get("编辑信息"):
            buf["editors_info"] = self.parse_editors_info(table_mapping["编辑信息"][-1].get("origin"))

        # 去空
        buf = {key: item for key, item in buf.items() if item != ""}
        yield EngJournalItem(**buf)

    @staticmethod
    def extract_chart_data(response: Response):
        """
        提取中科院分区数据
        :author:Mabin
        :param response:
        :return:
        """
        script_text = response.xpath('//script[contains(text(), "showecharts_historyjcr")]//text()').get()

        # 定位相关函数
        locate_march = re.search(r"showecharts_historyjcr.*?$", script_text, re.DOTALL)
        if not locate_march:
            return []
        locate_str = locate_march.group()

        # 提取年份数据
        years = re.findall(r"\d{4}-(\d{4})年度", locate_str)

        # 提取分区数据（找到对应函数的渲染数组）
        data_match = re.search(r'series\s:.*?data\s*:\s*\[([\d,\s]+)]', locate_str, re.DOTALL)
        if not data_match:
            return []

        # 获取第一个捕获组的内容
        data_matches = data_match.group(1)
        history_jcr = data_matches.split(",")

        # mapping合并
        year_mapping = dict(zip(years, history_jcr))

        # 修正数据信息（strip、2024年份修正为2025）
        buf = []
        for key, item in year_mapping.items():
            item = str(item).strip()
            if not item or item == "0":
                continue

            if key == "2024":
                # 2024年份修正为2025
                key = "2025"

            buf.append({
                "subject_quartile": f"{item}区",
                "year": key,
                "data_source": "中科院分区"
            })

        # 返回相关数据
        return buf

    def extract_cite_score(self, origin_html: str, thead_text: str):
        """
        提取CiteScore
        :author:Mabin
        :param origin_html:源HTML
        :param thead_text:表头信息
        :return:
        """
        if not origin_html:
            return {}

        # 提取年份信息
        year_text = re.search(r'(\d{4})年', thead_text)
        if not year_text:
            # 未能提取到年份信息
            return {}
        year_text = year_text.group(1)

        # 构造新的选择器
        analysis_selector = Selector(text=html.unescape(origin_html).strip())

        # 获取表头
        header_cells = analysis_selector.xpath('//th').getall()

        # 按列选取数据
        buf = {}
        for col_index in range(1, len(header_cells) + 1):
            # 对应的列的HTML
            column_item = analysis_selector.xpath(f'//td/table/tr/td[{col_index}]').get()

            # 对应列名
            header_name = BaseSelectorComponent.get_sub_sup_text(header_cells[col_index - 1])
            if header_name == "CiteScore排名":
                buf[header_name] = self.extract_cite_score_ranking(column_item, year_text)
            else:
                # 非CiteScore排名
                buf[header_name] = [
                    {
                        "value": BaseSelectorComponent.get_sub_sup_text(column_item),  # 分值
                        "year": year_text,
                    }
                ]

        return buf

    @staticmethod
    def extract_cite_score_ranking(origin_html: str, year_text: str):
        """
        提取CiteScore排名信息
        :author:Mabin
        :param origin_html:
        :param year_text:统计年份
        :return:
        """
        # 构造新的选择器
        analysis_selector = Selector(text=html.unescape(origin_html).strip())

        # 选择除首行外的每一行
        buf = []
        table_rows = analysis_selector.xpath('//table//tr[position() > 1]')
        for row_item in table_rows:
            # 学科
            parent_category = None
            sub_category = None
            subject_list = row_item.xpath('./td[1]//text()').getall()
            for subject_item in subject_list:
                if "大类：" in subject_item:
                    parent_category = str(subject_item).replace("大类：", "").strip()
                elif "小类：" in subject_item:
                    sub_category = str(subject_item).replace("小类：", "").strip()

            subject_quartile = BaseSelectorComponent.get_sub_sup_text(row_item.xpath('./td[2]').get())  # 分区
            ranking_str = BaseSelectorComponent.get_sub_sup_text(row_item.xpath('./td[3]').get()).replace(" ", "")  # 排名
            percentile = row_item.xpath(
                '//div[@class="layui-progress-bar"]/@lay-percent'
            ).get().rstrip("%").strip()  # 百分比

            # 记录相关数据
            buf.append({
                "category": parent_category,
                "subcategory": sub_category,
                "subject_quartile": subject_quartile,  # 分区
                "subject_rank": ranking_str,  # 排名
                "subject_percentile": percentile,  # 百分位
                "year": year_text,  # 统计年份
            })

        return buf

    def extract_jcr_info(self, origin_html: str, thead_text: str):
        """
        提取JCR数据
        :author:Mabin
        :param origin_html:
        :param thead_text:
        :return:
        """
        if not origin_html:
            return {}

        # 获取年份
        year_text = re.search(r'\d{4}-(\d{4})年', thead_text)
        if not year_text:
            # 未能提取到年份信息
            return {}
        year_text = year_text.group(1)

        # 构造新的选择器
        analysis_selector = Selector(text=html.unescape(origin_html).strip())

        # 分区等级
        subject_quartile = analysis_selector.xpath("//td/span/text()").get().strip()

        return {
            "jif": self.get_simple_jcr(
                analysis_selector.xpath('//table[.//td[contains(text(), "JIF")]]'),
                year_text=year_text
            ),  # 解析JIF指标学科分区
            "jci": self.get_simple_jcr(
                analysis_selector.xpath('//table[.//td[contains(text(), "JCI")]]'),
                year_text=year_text
            ),  # 解析JCI指标学科分区
            "subject_quartile": [
                {
                    "year": year_text,
                    "value": subject_quartile
                }
            ] if subject_quartile and subject_quartile != "0区" else []
        }

    @staticmethod
    def get_simple_jcr(analysis_selector, year_text: str):
        """
        解析JCR数据
        :author:Mabin
        :param analysis_selector:JCR表格所在选择器
        :param year_text:年份文本
        :return:
        """
        buf = []
        table_rows = analysis_selector.xpath('.//tr[position() > 1]')  # 跳过首行
        for row_item in table_rows:
            # 学科
            subject_info = BaseSelectorComponent.get_sub_sup_text(
                row_item.xpath('./td[1]').get()
            ).replace("学科：", "").strip()

            subject_quartile = BaseSelectorComponent.get_sub_sup_text(row_item.xpath('./td[3]').get())  # 分区
            ranking_str = BaseSelectorComponent.get_sub_sup_text(row_item.xpath('./td[4]').get()).replace(" ", "")  # 排名
            percentile = row_item.xpath(
                '//div[@class="layui-progress-bar"]/@lay-percent'
            ).get().rstrip("%").strip()  # 百分比

            # 记录相关数据
            buf.append({
                "category": subject_info,
                "subject_quartile": subject_quartile,  # 分区
                "subject_rank": ranking_str,  # 排名
                "subject_percentile": percentile,  # 百分位
                "year": year_text,  # 统计年份
            })

        return buf

    @staticmethod
    def get_zky_info(origin_html: str, thead_text: str):
        """
        解析中国科学院期刊分区的排名信息
        :author:Mabin
        :param origin_html:
        :param thead_text:
        :return:
        """
        if not origin_html:
            return {}

        # 提取年份信息
        year_text = re.search(r'(\d{4})年', thead_text)
        if not year_text:
            # 未能提取到年份信息
            return {}
        year_text = year_text.group(1)

        # 构造新的选择器
        analysis_selector = Selector(text=html.unescape(origin_html).strip())

        table_rows = analysis_selector.xpath('.//tr[position() > 1]')  # 跳过首行

        buf = []
        top_journal = False
        for row_item in table_rows:
            # 大类学科
            parent_category = row_item.xpath('./td[1]')
            parent_subject_name = parent_category.xpath('./text()').get()
            # 提取可见的分区信息
            large_category_partition = parent_category.xpath(
                './/span[not(contains(@style, "display:none"))]/text()'
            ).get()

            # 提取 Top 期刊
            top_journal_text = row_item.xpath('./td[3]/text()').get()
            if top_journal_text == "是":
                top_journal = True

            # 小类学科
            sub_sector = row_item.xpath('./td[2]//tr')
            for sub_item in sub_sector:
                sub_category = sub_item.xpath("./td[1]//text()").getall()

                # 纠正中英文
                sub_info = en_cn_correction(
                    text_list=sub_category,
                    chs_field_name="translate_name",
                    eng_field_name="subject_name",
                )

                # 提取可见的分区信息
                sub_category_partition = sub_item.xpath(
                    './td[2]//span[not(contains(@style, "display:none"))]/text()'
                ).get()
                # 记录相关数据
                buf.append({
                    "year": year_text,
                    "category": parent_subject_name,
                    "subcategory": sub_info["subject_name"],
                    "trans_subcategory": sub_info["translate_name"],
                    "sub_subject_quartile": sub_category_partition,
                    "subject_quartile": large_category_partition,
                })

        return {"data": buf, "top_journal": top_journal}

    def parse_journal_info(self, origin_html: str):
        """
        解析期刊版面信息
        :author:Mabin
        :param origin_html:原始HTML片段
        :return:
        """
        if not origin_html:
            return {}

        # 构造新的选择器
        analysis_selector = Selector(text=html.unescape(origin_html).strip())

        # ===== 提取相关链接 =====
        result = {
            "journal_aims": analysis_selector.xpath(f'//a[contains(@title, "期刊简介")]/@href').get(),  # 期刊简介链接
            "author_guidelines": analysis_selector.xpath(f'//a[contains(@title, "用户指南")]/@href').get(),  # 用户指南链接
            "editorial_board": analysis_selector.xpath(f'//a[contains(@title, "编辑团队")]/@href').get(),  # 编辑团队链接
            "review_process": analysis_selector.xpath(f'//a[contains(@title, "审稿流程")]/@href').get(),  # 审核流程链接
        }

        # 一次性获取所有 <b> 节点
        b_nodes = analysis_selector.xpath('//b')

        for b in b_nodes:
            b_text = b.xpath('text()').get()  # 获取 <b> 标签的文本
            if not b_text:
                continue

            # 获取 <b> 标签后的所有兄弟节点（直到下一个 <b> 或 <br>）
            siblings = b.xpath('./following-sibling::node()')
            sibling_text = ""
            for node in siblings:
                node_str = node.get()
                if '<br>' in node_str:  # 遇到下一个 <b> 或 <br> 时停止
                    break
                sibling_text += node_str

            # 清理文本
            sibling_text = re.sub(r'<a[^>]*>.*?</a>', '', sibling_text)  # 删除a标签及其内容
            sibling_text = BaseSelectorComponent.get_sub_sup_text(sibling_text)

            if "文章处理费" in b_text and "豁免" not in b_text:
                # 处理 APC
                apc_link = b.xpath('./following-sibling::a[1]/@href').get()
                apc_text = sibling_text.strip(" （;）")
                apc_amount, apc_currency = self.parse_money_string(apc_text) if apc_text else (None, None)
                result["apc"] = {
                    "text": apc_text or None,
                    "link": (apc_link or "").strip() or None,
                    "amount": apc_amount,
                    "currency": apc_currency
                }
            elif "豁免" in b_text:
                # 处理豁免链接
                waiver_link = b.xpath('./following-sibling::a[1]/@href').get()
                result["waiver_link"] = (waiver_link or "").strip() or None
            elif "其他费用" in b_text:
                # 其他费用
                result["other_fees"] = sibling_text or None
            elif "APC费用补充说明" in b_text:
                # APC 补充说明
                amount, currency = self.parse_money_string(sibling_text)  # 提取金额和货币（如 6500 元/页）
                result["apc_supplement"] = {
                    "text": sibling_text,
                    "amount": amount,
                    "currency": currency
                }
            elif "版面费" in b_text:
                # 版面费
                amount, currency = self.parse_money_string(sibling_text)  # 提取金额和货币（如 6500 元/页）
                result["fee"] = {
                    "text": sibling_text,
                    "amount": amount,
                    "currency": currency
                }

        return result

    @staticmethod
    def parse_money_string(text):
        """
        解析货币字符串：如 USD1050 → ('1050', 'USD')
        :author:Mabin
        :param text: 输入字符串
        :return: (amount, currency)
        """
        if not text:
            return None, None

        # 正则匹配：字母 + 数字
        pattern = r'([A-Za-z]+)(\d+)'
        match = re.search(pattern, text)
        if match:
            currency = match.group(1).upper()  # 货币（大写）
            amount = match.group(2)  # 金额
            return amount, currency
        else:
            # 尝试匹配：数字 + 中文货币
            pattern = r'(\d+)\s*([元]+)'
            match = re.search(pattern, text)
            if match:
                amount = match.group(1)
                currency = 'CNY'  # 默认人民币
                return amount, currency
            return None, None

    @staticmethod
    def parse_editors_info(origin_html: str):
        """
        解析编辑团队信息（基于位置关系：每组第一行是编辑信息，第二行是专业领域）
        :author:Mabin
        :param origin_html: 原始HTML
        :return: 按职位分组的编辑列表
        """
        if not origin_html:
            return {}

        selector = Selector(text=html.unescape(origin_html).strip())

        # 存储最终结果
        result = {}

        # 1. 提取所有 <b> 标签的文本（职位）
        position_nodes = selector.xpath('//b')
        positions = [pos.xpath('text()').get().strip() for pos in position_nodes if pos.xpath('text()').get()]

        # 2. 提取所有非 <br> 的文本行
        lines = selector.xpath('//text()[not(ancestor::br)]').getall()
        lines = [line.strip() for line in lines if line.strip()]

        # 3. 遍历每一行，动态分组
        current_position = None
        editors_in_current_position = []  # 当前职位下的所有编辑
        line_index_in_position = 0  # 当前职位下的行索引（0, 1, 2...）

        for line in lines:
            if line in positions:  # 如果是职位行
                # 保存上一个职位的数据
                if current_position and editors_in_current_position:
                    result[current_position] = editors_in_current_position

                # 切换到新职位
                current_position = line
                editors_in_current_position = []
                line_index_in_position = 0
            else:
                # 根据行索引判断是编辑信息还是专业领域
                if line_index_in_position % 2 == 0:  # 偶数行（0, 2, 4...）是编辑信息
                    editors_in_current_position.append({
                        "info": line,
                        "field": None
                    })
                else:  # 奇数行（1, 3, 5...）是专业领域
                    if editors_in_current_position:  # 确保有对应的编辑信息
                        editors_in_current_position[-1]["field"] = line

                line_index_in_position += 1

        # 保存最后一个职位的数据
        if current_position and editors_in_current_position:
            result[current_position] = editors_in_current_position

        return result
