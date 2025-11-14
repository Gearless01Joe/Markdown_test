# -*- coding: utf-8 -*-

"""
# @Time    : 2025/9/11 11:28
# @User  : Mabin
# @Description  :https://mjl.clarivate.com/期刊网站爬取
"""
import uuid
from scrapy.http import JsonRequest, JsonResponse
from src.spiders.base_spider import BaseSpider
# from src.items.other.detail_fields_item import DetailFieldsItem
from src.items.other.eng_journal_item import EngJournalItem, JOURNAL_OPEN_ACCESS


class ClarivateSpider(BaseSpider):
    name = 'clarivate_journal'
    allowed_domains = ["mjl.clarivate.com"]
    base_url = "https://mjl.clarivate.com/"
    page_size = 1000  # 每页数量

    """
    自定义配置
    """
    custom_settings = {
        'ITEM_PIPELINES': {
            # 'src.pipelines.storage.detail_fields_pipeline.DetailFieldsPipeline': 301,
            'src.pipelines.storage.eng_journal_pipeline.EngJournalPipeline': 301,
        },
        # 'DOWNLOAD_DELAY': 3,  # 爬取请求之间的延迟时间，以秒为单位
        'CONCURRENT_REQUESTS': 3,  # 并发量
    }

    def start_requests(self):
        """
        初始化爬虫
        :author:Mabin
        :return:
        """
        # 执行初始化请求
        yield self._organ_list_req(
            page_num=1,
            page_size=10,
            callback=self.parse
        )

    def parse(self, response: JsonResponse, **kwargs):
        """
        解析数据
        :author:Mabin
        :param response: 响应对象
        :param kwargs:
        :return:
        """
        # 获取请求结果
        json_res = response.json()

        # 获取分页情况
        total_records = json_res.get("totalRecords")
        if not total_records:
            raise ValueError("列表页接口未查询到相关分页数据！")

        total_pages = (total_records + self.page_size - 1) // self.page_size  # 计算总页数
        for page_num in range(1, total_pages + 1):
            # 请求分页数据
            print(f"正在请求第 {page_num}/{total_pages} 页数据...")
            yield self._organ_list_req(
                page_num=page_num,
                page_size=self.page_size,
                callback=self.parse_list_data
            )

    def parse_list_data(self, response: JsonResponse, **kwargs):
        """
        解析列表页
        :author:Mabin
        :param response:
        :param kwargs:
        :return:
        """
        # 获取请求结果
        json_res = response.json()

        # 遍历期刊信息
        for journal_item in json_res.get("journalProfiles", []):
            journal_profile = journal_item.get("journalProfile", {})

            # 获取期刊索引
            index_list = []
            for index_item in journal_profile.get("products", []):
                normalized_name = self._normalized_index_name(index_item.get("description"))
                if not normalized_name:
                    continue

                # yield DetailFieldsItem(
                #     data_key=index_item.get("description"),
                #     data_value=index_item.get("productCode"),
                #     original_html=journal_profile,
                # )
                index_list.append(normalized_name)

            # 组织item
            yield EngJournalItem(
                journal_name=journal_profile.get("publicationTitle"),
                abbr_name=journal_profile.get("publicationTitle20"),
                issn=journal_profile.get("issn"),
                eissn=journal_profile.get("eissn"),
                year=journal_profile.get("publicationStartYear"),
                country=journal_profile.get("country"),
                language=";".join(journal_profile.get("publicationLanguages", [])) or None,
                publisher=journal_profile.get("publisherName"),
                publisher_address=journal_profile.get("publisherAddress"),
                publisher_website=journal_profile.get("publisherURL"),
                index_list=index_list,
                original_html=journal_profile,
                openaccess=JOURNAL_OPEN_ACCESS["open"] if journal_profile.get("openAccess") else JOURNAL_OPEN_ACCESS[
                    "not_open"],
            )

    @staticmethod
    def _organ_list_req(page_num, page_size, callback):
        """
        组织列表页请求链接
        :author:Mabin
        :param page_num:
        :param page_size:
        :param callback:
        :return:
        """
        return JsonRequest(
            url='https://mjl.clarivate.com/api/mjl/jprof/public/rank-search',
            data={
                "searchValue": "",
                "pageNum": page_num,
                "pageSize": page_size,
                "sortOrder": [{"name": "TITLE", "order": "ASC"}],
                "filters": [
                    {
                        "filterName": "COVERED_LATEST_JEDI",
                        "matchType": "BOOLEAN_EXACT",
                        "caseSensitive": False,
                        "values": [{"type": "VALUE", "value": "true"}]
                    },
                    {
                        "filterName": "PRODUCT_CODE",
                        "matchType": "TEXT_EXACT",
                        "caseSensitive": False,
                        "values": [
                            {"type": "VALUE", "value": "D"}, {"type": "VALUE", "value": "J"},
                            {"type": "VALUE", "value": "SS"}, {"type": "VALUE", "value": "H"},
                            {"type": "VALUE", "value": "EX"}, {"type": "VALUE", "value": "A"},
                            {"type": "VALUE", "value": "Y"}, {"type": "VALUE", "value": "BC"},
                            {"type": "VALUE", "value": "C"}, {"type": "VALUE", "value": "EC"},
                            {"type": "VALUE", "value": "T"}, {"type": "VALUE", "value": "P"},
                            {"type": "VALUE", "value": "S"}, {"type": "VALUE", "value": "B"},
                            {"type": "VALUE", "value": "BA"}, {"type": "VALUE", "value": "BP"},
                            {"type": "VALUE", "value": "B1"}, {"type": "VALUE", "value": "B2"},
                            {"type": "VALUE", "value": "B3"}, {"type": "VALUE", "value": "B4"},
                            {"type": "VALUE", "value": "RR"}, {"type": "VALUE", "value": "CR"},
                            {"type": "VALUE", "value": "ES"}, {"type": "VALUE", "value": "I"},
                            {"type": "VALUE", "value": "B7"}
                        ]
                    }
                ],
                "searchIdentifier": f"{uuid.uuid4()}"
            },
            callback=callback,
            dont_filter=True,
            headers={
                "authorization": "Bearer",
            }
        )

    @staticmethod
    def _normalized_index_name(name_string):
        """
        标准化名称信息
        :author:Mabin
        :param name_string:名称信息
        :return:
        """
        # 定义映射关系
        replacements = {
            "Emerging Sources Citation Index": "Emerging Sources Citation Index",
            "Arts & Humanities Citation Index": "Arts&Humanities Citation Index",
            "Science Citation Index Expanded": "Science Citation Index Expanded",
            "CC/Physical, Chemical & Earth Sciences": "Current Contents Physical, Chemical&Earth Sciences",
            "Essential Science Indicators": "Essential Science Indicators",
            "Journal Citation Reports Science": "Journal Citation Reports Science",
            "Biological Abstracts": "Biological Abstracts",
            "BIOSIS Previews/BIOSIS Citation Index": "BIOSIS Previews/BIOSIS Citation Index",
            "Current Contents Life Sciences": "Current Contents Life Sciences",
            "CC/Engineering, Computing & Technology": "Current Contents Engineering, Computing&Technology",
            "Web Of Science Expanded": "Web Of Science Expanded",
            "CC/Arts & Humanities": "Current Contents Arts&Humanities",
            "Zoological Record": "Zoological Record",
            "Journal Citation Reports Social Sciences": "Journal Citation Reports Social Sciences",
            "Social Sciences Citation Index": "Social Sciences Citation Index",
            "Scielo": "Scielo",
            "CC/Clinical Medicine": "Current Contents Clinical Medicine",
            "Biosis Reviews Reports And Meetings": "Biosis Reviews Reports And Meetings",
            "CC/Social And Behavioral Sciences": "Current Contents Social And Behavioral Sciences",
            "Business Collection": "Current Contents Business Collection",
            "CC/Agriculture, Biology & Environmental Sciences": "Current Contents Agriculture, Biology&Environmental Sciences",
            "Index To Scientific Reviews": "Index To Scientific Reviews",
            "Reaction Citation Index": "Reaction Citation Index",
            "Electronics & Telecommunications Collection": "Current Contents Electronics&Telecommunications Collection",
            "Index Chemicus": "Index Chemicus",
            "Book Social Science & Humanities Citation Index": "Book Social Science & Humanities Citation Index",
        }

        return replacements.get(name_string, None)
