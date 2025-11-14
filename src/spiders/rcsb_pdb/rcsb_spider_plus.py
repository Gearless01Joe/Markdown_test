# -*- coding: utf-8 -*-

"""
# @Time    : 2025/11/07 11:15
# @User  : 刘子都
# @Description  : RCSB PDB Plus完整爬虫（优化版）
#                 改进：
#                 1. 完全基于API，去除HTML依赖
#                 2. 批次大小从25提升到100
#                 3. 字段增强（分子量、全名、详细信息）
#                 4. 简化为3层结构
"""

import scrapy
import json
from src.items.other.rcsb_pdb_item_plus import PdbItemPlus


class PDBCompletePlusSpider(scrapy.Spider):
    """
    
    数据获取流程（3层）：
    1. Search API: 获取PDB ID列表（100个/批次）
    2. GraphQL API: 获取7个字段（Organism、Expression_System、Mutation、Macromolecule、Ligands等）
    3. REST API: 获取其他所有字段
       - Entry API: 基本信息、实验数据、分子组成
       - Assembly API: 对称性和化学计量
    """
    
    name = 'rcsb_pdb_plus'
    allowed_domains = ['rcsb.org', 'data.rcsb.org', 'files.rcsb.org']
    start_urls = ['https://www.rcsb.org/']

    custom_settings = {
        # ========== 并发控制 ==========
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,
        'RANDOMIZE_DOWNLOAD_DELAY': False,
        
        # ========== 超时和重试 ==========
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 60,
        
        # ========== 性能优化 ==========
        'DNSCACHE_ENABLED': True,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        
        # ========== Pipeline配置 ==========
        'ITEM_PIPELINES': {
            'src.pipelines.file_download_pipeline.FileDownloadPipeline': 200,
            'src.pipelines.file_replacement_pipeline.FileReplacementPipeline': 300,
            'src.pipelines.storage.rcsb_pdb_pipeline_plus.RcsbPdbPipelinePlus': 400,
        },
        
        # ========== 文件存储配置 ==========
        'FILES_STORE': 'runtime/temp',
        'IMAGES_STORE': 'runtime/temp',
        'IMAGES_THUMBS': {},
        'IMAGES_MIN_HEIGHT': 0,
        'IMAGES_MIN_WIDTH': 0,
        'MEDIA_ALLOW_REDIRECTS': True,
    }

    def __init__(self, max_targets=None, start_from=None, *args, **kwargs):
        """
        初始化爬虫
        
        Args:
            max_targets: 本次爬取的目标数量（默认3）
            start_from: 起始位置（默认0）
        """
        super(PDBCompletePlusSpider, self).__init__(*args, **kwargs)
        
        # API端点
        self.api_base_url = "https://search.rcsb.org/rcsbsearch/v2/query"
        self.structures_api_base = "https://data.rcsb.org/rest/v1/core"
        self.graphql_api_url = "https://data.rcsb.org/graphql"
        
        # 爬取控制（批次大小提升到100）
        self.batch_size = 100  # ← 从25提升到100
        self.start_from = int(start_from) if start_from else 0
        self.current_batch = self.start_from // self.batch_size
        self.max_targets = int(max_targets) if max_targets else 3
        
        # 状态跟踪
        self.collected_ids = set()
        self.pending_requests = 0
        self.requested_count = 0
        self.processed_count = 0
        
        # 失败统计
        self.failed_details = []
        
        # 检查Pillow
        try:
            import PIL
            self.logger.info(f"✅ Pillow已安装，版本: {PIL.__version__}")
        except ImportError:
            self.logger.warning("⚠️ Pillow未安装！")
    #
        # history_data_middleware会注入is_seen方法
        self.is_seen = lambda key: False
    
    def generate_unique_key(self, doc):
        """为history_data_middleware生成唯一标识"""
        return doc.get('PDB_ID', str(doc.get('_id', '')))
    
    # ========== 错误处理 ==========
    #
    def handle_api_error(self, failure):
        """处理API请求失败"""
        pdb_id = failure.request.meta.get('pdb_id', 'Unknown')
        self.logger.error(f"❌ API请求 {pdb_id} 失败: {failure.value}")
        self._record_failure(pdb_id, 'API请求', str(failure.value)[:200])
    
    def _record_failure(self, pdb_id, fail_type, reason):
        """记录失败详情"""
        self.pending_requests -= 1
        self.failed_details.append({
            'pdb_id': pdb_id,
            'type': fail_type,
            'reason': reason
        })
    
    def closed(self, reason):
        """爬虫关闭时输出失败详情"""
        if self.failed_details:
            self.logger.info("=" * 80)
            self.logger.info("📋 失败汇总（按类型）：")
            
            failures_by_type = {}
            for fail in self.failed_details:
                fail_type = fail['type']
                if fail_type not in failures_by_type:
                    failures_by_type[fail_type] = []
                failures_by_type[fail_type].append(fail['pdb_id'])
            
            for fail_type, pdb_ids in failures_by_type.items():
                unique_ids = list(set(pdb_ids))
                self.logger.info(f"  {fail_type}: {', '.join(unique_ids)}")
            
            self.logger.info("=" * 80)
        else:
            self.logger.info("🎊 所有PDB结构均处理成功！")

    # ========== 数据采集流程 ==========
# restructure 注释风格
    def parse(self, response):
        """第1层：通过Search API获取PDB ID列表"""
        self.logger.info(
            f"开始获取PDB结构列表，"
            f"目标数量: {self.max_targets}, "
            f"起始位置: {self.start_from}, "
            f"批次大小: {self.batch_size}")
# 加注释
        query_data = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_id",
                    "operator": "exists"
                }
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {
                    "start": self.start_from,
                    "rows": self.batch_size  # ← 100个/批次
                },
                "scoring_strategy": "combined",
                "sort": [{
                    "sort_by": "rcsb_accession_info.initial_release_date",
                    "direction": "desc"
                }],
                "return_all_hits": False
            }
        }

        yield scrapy.Request(
            url=self.api_base_url,
            method='POST',
            body=json.dumps(query_data),
            headers={'Content-Type': 'application/json'}, #
            callback=self.parse_api_structure_list,
            meta={'batch_number': self.current_batch},
            dont_filter=True
        )

    def parse_api_structure_list(self, response):
        """解析Search API响应，获取PDB ID列表"""
        batch_number = response.meta['batch_number']
        # response.json
        self.logger.info(f"处理第{batch_number + 1}批结构数据")

        try:
            data = json.loads(response.text)

            if 'result_set' not in data or not data['result_set']:
                self.logger.info("没有更多结构数据，爬取完成")
                return

            pdb_ids = [result['identifier'] for result in data['result_set']]
            self.logger.info(f"本批次获取到{len(pdb_ids)}个结构")

            if self.requested_count >= self.max_targets:
                self.logger.info(f"已达到最大目标数量 {self.max_targets}")
                return

            remaining_targets = self.max_targets - self.requested_count
            ids_to_process = pdb_ids[:remaining_targets]

            self.logger.info(f"本批次将处理{len(ids_to_process)}个结构（剩余目标：{remaining_targets}）")
            self.pending_requests += len(ids_to_process)

            # 为每个PDB ID启动GraphQL数据采集
            for pdb_id in ids_to_process:
                # 去重检查
                if pdb_id in self.collected_ids:
                    self.logger.info(f"⚠️ 跳过重复的PDB ID（内存）: {pdb_id}")
                    self.pending_requests -= 1
                    continue
                
                if self.is_seen(pdb_id):
                    self.logger.info(f"⚠️ 跳过已爬取的PDB ID（历史）: {pdb_id}")
                    self.pending_requests -= 1
                    continue

                self.collected_ids.add(pdb_id)
                self.requested_count += 1

                # 第2层：直接请求GraphQL（跳过HTML）
                graphql_query = {
                    "query": f"""
                    {{
                      entry(entry_id: "{pdb_id}") {{
                        polymer_entities {{
                          rcsb_id
                          
                          rcsb_polymer_entity {{
                            pdbx_description
                            formula_weight
                          }}
                          
                          entity_poly {{
                            type
                            pdbx_strand_id
                          }}
                          
                          rcsb_entity_source_organism {{
                            ncbi_scientific_name
                          }}
                          
                          rcsb_entity_host_organism {{
                            ncbi_scientific_name
                          }}
                          
                          rcsb_polymer_entity_feature {{
                            type
                            name
                          }}
                        }}
                        
                        nonpolymer_entities {{
                          pdbx_entity_nonpoly {{
                            comp_id
                            name
                          }}
                        }}
                      }}
                    }}
                    """
                }
                
                yield scrapy.Request(
                    url=self.graphql_api_url,
                    method='POST',
                    body=json.dumps(graphql_query),
                    headers={'Content-Type': 'application/json'},
                    callback=self.parse_graphql_all,
                    meta={'pdb_id': pdb_id},
                    dont_filter=True,
                    errback=self.handle_api_error
                )

            # 判断是否需要获取下一批
            remaining_after_batch = self.max_targets - self.requested_count
# 封装下一批的请求
            if remaining_after_batch > 0:
                self.current_batch += 1
                next_start = self.start_from + self.requested_count
                self.logger.info(
                    f"📋 需要获取下一批数据（批次 {self.current_batch + 1}）"
                    f"起始位置: {next_start}")

                query_data = {
                    "query": {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_id",
                            "operator": "exists"
                        }
                    },
                    "return_type": "entry",
                    "request_options": {
                        "paginate": {
                            "start": next_start,
                            "rows": min(self.batch_size, remaining_after_batch)
                        },
                        "scoring_strategy": "combined",
                        "sort": [{
                            "sort_by": "rcsb_accession_info.initial_release_date",
                            "direction": "desc"
                        }]
                    }
                }

                yield scrapy.Request(
                    url=self.api_base_url,
                    method='POST',
                    body=json.dumps(query_data),
                    headers={'Content-Type': 'application/json'},
                    callback=self.parse_api_structure_list,
                    meta={'batch_number': self.current_batch},
                    dont_filter=True
                )
# trycatch
            else:
                self.logger.info(f"✅ 所有批次请求已发出，已请求数量：{self.requested_count}/{self.max_targets}")

        except Exception as e:
            self.logger.error(f"解析结构列表API时出错: {e}")

    def parse_graphql_all(self, response):
        """第2层：从GraphQL提取7个字段（扩展版）"""
        pdb_id = response.meta['pdb_id']

        if self.processed_count >= self.max_targets:
            self.logger.info(f"已达到上限，跳过处理 {pdb_id}")
            self.pending_requests -= 1
            return

        try:
            graphql_data = response.json()
            
            # 检查GraphQL错误
            if 'errors' in graphql_data:
                errors = '; '.join([e.get('message', str(e)) for e in graphql_data['errors']])
                self.logger.warning(f"GraphQL返回错误: {errors}")
            
            # 提取GraphQL数据
            graphql_extracted = self.extract_from_graphql(graphql_data, pdb_id)
            
            self.logger.info(f"✅ GraphQL获取 {pdb_id} 的7个字段")
            
            # 第3层：请求Entry API
            api_url = f"{self.structures_api_base}/entry/{pdb_id}"
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_entry_api,
                meta={'pdb_id': pdb_id, 'graphql_data': graphql_extracted},
                dont_filter=True,
                errback=self.handle_api_error
            )
                
        except Exception as e:
            self.logger.error(f"❌ 解析GraphQL {pdb_id} 时出错: {e}")
            self._record_failure(pdb_id, 'GraphQL解析', str(e)[:200])
    
    def parse_entry_api(self, response):
        """第3层A：从Entry API提取基本信息和实验数据"""
        pdb_id = response.meta['pdb_id']
        graphql_data = response.meta.get('graphql_data', {})

        if self.processed_count >= self.max_targets:
            self.logger.info(f"已达到上限，跳过处理 {pdb_id}")
            self.pending_requests -= 1
            return

        try:
            entry_data = response.json()
            
            # 提取Entry API数据
            entry_extracted = self.extract_data_from_entry_api(entry_data)
            
            # 合并GraphQL数据和Entry数据
            combined_data = {**graphql_data, **entry_extracted}
            
            self.logger.info(f"✅ Entry API获取 {pdb_id} 的数据")
            
            # 第3层B：请求Assembly API获取对称性数据
            assembly_url = f"{self.structures_api_base}/assembly/{pdb_id}/1"
            yield scrapy.Request(
                url=assembly_url,
                callback=self.parse_assembly_api,
                meta={'pdb_id': pdb_id, 'combined_data': combined_data},
                dont_filter=True,
                errback=self.handle_api_error
            )

        except Exception as e:
            self.logger.error(f"❌ 解析Entry API {pdb_id} 时出错: {e}")
            self._record_failure(pdb_id, 'Entry API解析', str(e)[:200])
    
    def parse_assembly_api(self, response):
        """第3层B：从Assembly API提取对称性数据"""
        pdb_id = response.meta['pdb_id']
        combined_data = response.meta.get('combined_data', {})

        try:
            assembly_data = response.json()
            
            # 提取Assembly数据
            assembly_extracted = self.extract_from_assembly_api(assembly_data)
            
            # 创建Item并设置PDB_ID
            item = PdbItemPlus()
            
            # 初始化所有字段为None
            for field in PdbItemPlus.fields.keys():
                if field not in ['file_urls', 'files', 'page_url', 'cif_file', 'validation_image', 'PDB_ID']:
                    item[field] = None
            
            # 设置PDB_ID（必须在初始化之后）
            item['PDB_ID'] = pdb_id
            
            # 合并所有数据
            for key, value in combined_data.items():
                item[key] = value
            
            for key, value in assembly_extracted.items():
                item[key] = value
            
            # 设置BaseItem基础字段
            item['page_url'] = f"https://www.rcsb.org/structure/{pdb_id}"
            
            # 设置文件下载
            cif_url = f"https://files.rcsb.org/download/{pdb_id}.cif"
            image_url = f"https://files.rcsb.org/validation/view/{pdb_id.lower()}_multipercentile_validation.png"
            
            item['file_urls'] = [cif_url, image_url]
            item['cif_file'] = cif_url
            item['validation_image'] = image_url

            self.processed_count += 1
            self.pending_requests -= 1

            self.logger.info(
                f"✅ 成功获取结构 {pdb_id} 的数据 "
                f"(进度: {self.processed_count}/{self.max_targets})")

            yield item

        except Exception as e:
            self.logger.error(f"❌ 解析Assembly API {pdb_id} 时出错: {e}")
            self._record_failure(pdb_id, 'Assembly API解析', str(e)[:200])

    # ========== GraphQL数据提取（扩展版）==========
# 重复了
    def extract_from_graphql(self, graphql_data, pdb_id):
        """
        从GraphQL提取7个字段（扩展版）
        
        提取内容：
        1. Organism (来源物种)
        2. Expression_System (表达系统)
        3. Mutation (序列突变，包含详情)
        4. Macromolecule (大分子，包含分子量、类型、链)
        5. unique_Ligands (配体，包含化学全名)
        """
        extracted = {}
        
        if 'data' not in graphql_data or not graphql_data['data']:
            return extracted
        
        entry = graphql_data['data'].get('entry')
        if not entry:
            return extracted
        
        # 提取Polymer Entities数据
        if 'polymer_entities' in entry and entry['polymer_entities']:
            self._extract_polymer_data(entry['polymer_entities'], extracted)
        
        # 提取NonPolymer Entities数据
        if 'nonpolymer_entities' in entry and entry['nonpolymer_entities']:
            self._extract_nonpolymer_data(entry['nonpolymer_entities'], extracted)
        
        return extracted
    
    def _extract_polymer_data(self, polymer_entities, extracted):
        """从polymer_entities提取数据"""
        
        organisms = []
        expression_systems = []
        macromolecules = []
        mutation_count = 0
        mutation_names = set()
        
        for poly in polymer_entities:
            # 1. Organism
            if poly.get('rcsb_entity_source_organism'):
                for org in poly['rcsb_entity_source_organism']:
                    if org.get('ncbi_scientific_name'):
                        organisms.append(org['ncbi_scientific_name'])
            
            # 2. Expression_System
            if poly.get('rcsb_entity_host_organism'):
                for host in poly['rcsb_entity_host_organism']:
                    if host.get('ncbi_scientific_name'):
                        expression_systems.append(host['ncbi_scientific_name'])
            
            # 3. Macromolecule (增强版：包含分子量、类型、链)
            if poly.get('rcsb_polymer_entity'):
                desc = poly['rcsb_polymer_entity'].get('pdbx_description', '')
                weight = poly['rcsb_polymer_entity'].get('formula_weight')
                poly_type = poly.get('entity_poly', {}).get('type', '')
                chains = poly.get('entity_poly', {}).get('pdbx_strand_id', '')
                
                if desc:
                    # 构建增强格式：描述 (分子量, 类型, 链)
                    parts = [desc]
                    
                    info_parts = []
                    if weight:
                        info_parts.append(f"{weight} kDa")
                    if poly_type:
                        info_parts.append(poly_type)
                    if chains:
                        info_parts.append(f"Chains: {chains}")
                    
                    if info_parts:
                        enhanced = f"{desc} ({', '.join(info_parts)})"
                    else:
                        enhanced = desc
                    
                    macromolecules.append(enhanced)
            
            # 4. Mutation (增强版：包含类型和数量)
            if poly.get('rcsb_polymer_entity_feature'):
                for feature in poly['rcsb_polymer_entity_feature']:
                    if feature.get('type', '').lower() == 'mutation':
                        mutation_count += 1
                        if feature.get('name'):
                            mutation_names.add(feature['name'])
        
        # 保存提取结果
        if organisms:
            extracted['Organism'] = ', '.join(set(organisms))
        
        if expression_systems:
            extracted['Expression_System'] = ', '.join(set(expression_systems))
        
        if macromolecules:
            extracted['Macromolecule'] = ', '.join(macromolecules)
        
        # Mutation增强版
        if mutation_count > 0:
            mutation_names_str = ', '.join(mutation_names) if mutation_names else 'mutation'
            extracted['Mutation'] = f"Yes ({mutation_names_str} x{mutation_count})"
        else:
            extracted['Mutation'] = "No"
    
    def _extract_nonpolymer_data(self, nonpolymer_entities, extracted):
        """从nonpolymer_entities提取配体数据（增强版）"""
        
        ligands = []
        
        for nonpoly in nonpolymer_entities:
            if nonpoly.get('pdbx_entity_nonpoly'):
                comp_id = nonpoly['pdbx_entity_nonpoly'].get('comp_id', '')
                name = nonpoly['pdbx_entity_nonpoly'].get('name', '')
                
                if comp_id:
                    # 增强格式：符号 (全名)
                    if name:
                        ligand_str = f"{comp_id} ({name})"
                    else:
                        ligand_str = comp_id
                    
                    ligands.append(ligand_str)
        
        if ligands:
            extracted['unique_Ligands'] = ', '.join(ligands)

    # ========== Entry API数据提取 ==========

    def extract_data_from_entry_api(self, data):
        """从Entry API提取数据"""
        extracted = {}

        try:
            # 基本信息
            self._extract_basic_info(data, extracted)
            
            # Macromolecule_Content字典（扩展版）
            self._extract_macromolecule_content_extended(data, extracted)
            
            # Experimental_Data_Snapshot
            self._extract_experimental_data(data, extracted)

        except Exception as e:
            extracted['api_extraction_error'] = str(e)

        return extracted
    
    def _extract_basic_info(self, data, extracted):
        """提取基本信息"""
        # 标题
        if 'struct' in data and 'title' in data['struct']:
            extracted['Title'] = data['struct']['title']
        
        # DOI
        if 'database2' in data and data['database2']:
            for db_entry in data['database2']:
                if 'pdbx_doi' in db_entry:
                    extracted['PDB_DOI'] = db_entry['pdbx_doi']
                    break
# 生成式    .get.or-设置默认值
        # 分类
        if 'struct_keywords' in data and 'pdbx_keywords' in data['struct_keywords']:
            extracted['Classification'] = data['struct_keywords']['pdbx_keywords']
        
        # 日期
        if 'rcsb_accession_info' in data:
            accession_info = data['rcsb_accession_info']
            extracted['Deposited'] = accession_info.get('deposit_date')
            extracted['Released'] = accession_info.get('initial_release_date')
        
        # 作者
        if 'audit_author' in data and data['audit_author']:
            authors = [author['name'] for author in data['audit_author'] if 'name' in author]
            if authors:
                extracted['Deposition_Author'] = ', '.join(authors)
        
        # PubMed ID
        if 'citation' in data and data['citation']:
            for citation in data['citation']:
                if 'pdbx_database_id_pub_med' in citation:
                    extracted['PMID'] = citation['pdbx_database_id_pub_med']
                    break
    
    def _extract_macromolecule_content_extended(self, data, extracted):
        """提取Macromolecule_Content字典（扩展版）"""
        if 'rcsb_entry_info' not in data:
            return
        
        entry_info = data['rcsb_entry_info']
        macromolecule_content = {}
        
        # 原有字段
        macromolecule_content['Total_Structure_Weight'] = entry_info.get('molecular_weight')
        macromolecule_content['Atom_Count'] = entry_info.get('deposited_atom_count')
        macromolecule_content['Modeled_Residue_Count'] = entry_info.get('deposited_modeled_polymer_monomer_count')
        macromolecule_content['Deposited_Residue_Count'] = entry_info.get('deposited_polymer_monomer_count')
        macromolecule_content['Unique_Protein_Chains'] = entry_info.get('polymer_entity_count')
        
        # 扩展字段（新增！）
        macromolecule_content['Solvent_Atom_Count'] = entry_info.get('deposited_solvent_atom_count')
        macromolecule_content['Model_Count'] = entry_info.get('deposited_model_count')
        macromolecule_content['Polymer_Composition'] = entry_info.get('polymer_composition')
        macromolecule_content['Nonpolymer_Entity_Count'] = entry_info.get('nonpolymer_entity_count')
        
        if macromolecule_content:
            extracted['Macromolecule_Content'] = macromolecule_content
    
    def _extract_experimental_data(self, data, extracted):
        """根据实验方法动态提取Experimental_Data_Snapshot"""
        experimental_data = {}
        
        # 提取实验方法
        if 'exptl' in data and data['exptl']:
            methods = [expt.get('method') for expt in data['exptl'] if expt.get('method')]
            if methods:
                experimental_data['Experimental_Method'] = ', '.join(methods)
        
        exp_method = experimental_data.get('Experimental_Method', '').upper()
        
        # 根据实验方法提取对应字段
        if any(method in exp_method for method in ['X-RAY', 'NEUTRON', 'ELECTRON CRYSTALLOGRAPHY']):
            self._extract_diffraction_data(data, experimental_data)
        elif 'ELECTRON MICROSCOPY' in exp_method or 'EM' in exp_method:
            self._extract_em_data(data, experimental_data)
        elif 'NMR' in exp_method:
            self._extract_nmr_data(data, experimental_data)
        elif 'POWDER DIFFRACTION' in exp_method or 'FIBER DIFFRACTION' in exp_method:
            self._extract_powder_fiber_data(data, experimental_data)
        
        if experimental_data:
            extracted['Experimental_Data_Snapshot'] = experimental_data
    
    def _extract_diffraction_data(self, data, experimental_data):
        """提取衍射法数据"""
        # Resolution
        if 'rcsb_entry_info' in data and 'diffrn_resolution_high' in data['rcsb_entry_info']:
            resolution_info = data['rcsb_entry_info']['diffrn_resolution_high']
            experimental_data['Resolution'] = resolution_info.get('value') if isinstance(resolution_info, dict) else resolution_info
        
        # R-Values
        r_free_values = []
        r_work_values = []
        r_obs_values = []
        
        if 'refine' in data and data['refine']:
            refine_list = data['refine'] if isinstance(data['refine'], list) else [data['refine']]
            
            if 'Resolution' not in experimental_data and refine_list:
                experimental_data['Resolution'] = refine_list[0].get('ls_dres_high')
            
            refine_data = refine_list[0]
            
            if refine_data.get('ls_rfactor_rfree') is not None:
                r_free_values.append(('Depositor', refine_data['ls_rfactor_rfree']))
            
            if refine_data.get('ls_rfactor_rwork') is not None:
                r_work_values.append(('Depositor', refine_data['ls_rfactor_rwork']))
            
            if refine_data.get('ls_rfactor_obs') is not None:
                r_obs_values.append(('Depositor', refine_data['ls_rfactor_obs']))
        
        if 'pdbx_vrpt_summary_diffraction' in data and data['pdbx_vrpt_summary_diffraction']:
            vrpt_diff_list = data['pdbx_vrpt_summary_diffraction']
            if isinstance(vrpt_diff_list, list) and vrpt_diff_list:
                vrpt_diff = vrpt_diff_list[0]
                
                if vrpt_diff.get('dccrfree') is not None:
                    r_free_values.append(('DCC', vrpt_diff['dccrfree']))
                
                if vrpt_diff.get('dcc_r') is not None:
                    r_work_values.append(('DCC', vrpt_diff['dcc_r']))
        
        if r_free_values:
            experimental_data['R-Value Free'] = r_free_values
        if r_work_values:
            experimental_data['R-Value Work'] = r_work_values
        if r_obs_values:
            experimental_data['R-Value Observed'] = r_obs_values
    
    def _extract_em_data(self, data, experimental_data):
        """提取电子显微镜数据"""
        if 'em3d_reconstruction' in data and data['em3d_reconstruction']:
            em_recon = data['em3d_reconstruction'][0] if isinstance(data['em3d_reconstruction'], list) else data['em3d_reconstruction']
            experimental_data['Resolution'] = em_recon.get('resolution')
        
        if 'em_experiment' in data:
            em_exp = data['em_experiment']
            experimental_data['Aggregation State'] = em_exp.get('aggregation_state')
            experimental_data['Reconstruction Method'] = em_exp.get('reconstruction_method')
    
    def _extract_nmr_data(self, data, experimental_data):
        """提取NMR数据"""
        if 'pdbx_nmr_ensemble' in data:
            nmr_data = data['pdbx_nmr_ensemble']
            experimental_data['Conformers Calculated'] = nmr_data.get('conformers_calculated_total_number')
            experimental_data['Conformers Submitted'] = nmr_data.get('conformers_submitted_total_number')
        
        if 'pdbx_nmr_representative' in data:
            nmr_rep = data['pdbx_nmr_representative']
            experimental_data['Selection Criteria'] = nmr_rep.get('selection_criteria')
    
    def _extract_powder_fiber_data(self, data, experimental_data):
        """提取粉末/纤维衍射数据"""
        if 'rcsb_entry_info' in data and 'diffrn_resolution_high' in data['rcsb_entry_info']:
            resolution_info = data['rcsb_entry_info']['diffrn_resolution_high']
            experimental_data['Resolution'] = resolution_info.get('value') if isinstance(resolution_info, dict) else resolution_info
# 切分太碎
    def _extract_nonpolymer_data(self, nonpolymer_entities, extracted):
        """从nonpolymer_entities提取配体数据（增强版）"""
        ligands = []
        
        for nonpoly in nonpolymer_entities:
            if nonpoly.get('pdbx_entity_nonpoly'):
                comp_id = nonpoly['pdbx_entity_nonpoly'].get('comp_id', '')
                name = nonpoly['pdbx_entity_nonpoly'].get('name', '')
                
                if comp_id:
                    # 增强格式：符号 (全名)
                    if name:
                        ligand_str = f"{comp_id} ({name})"
                    else:
                        ligand_str = comp_id
                    
                    ligands.append(ligand_str)
        
        if ligands:
            extracted['unique_Ligands'] = ', '.join(ligands)

    # ========== Assembly API数据提取 ==========

    def extract_from_assembly_api(self, data):
        """从Assembly API提取对称性和化学计量"""
        extracted = {}
        
        if 'rcsb_struct_symmetry' not in data:
            return extracted
        
        # 查找kind="Global Symmetry"的数据
        for sym_data in data['rcsb_struct_symmetry']:
            if sym_data.get('kind') == 'Global Symmetry':
                # Global_Symmetry
                sym_type = sym_data.get('type', '')
                symbol = sym_data.get('symbol', '')
                if sym_type and symbol:
                    extracted['Global_Symmetry'] = f"{sym_type} - {symbol}"
                
                # Global_Stoichiometry
                oligomeric_state = sym_data.get('oligomeric_state', '')
                stoichiometry = sym_data.get('stoichiometry', [])
                
                if oligomeric_state and stoichiometry:
                    stoich_str = ', '.join(stoichiometry) if isinstance(stoichiometry, list) else stoichiometry
                    extracted['Global_Stoichiometry'] = f"{oligomeric_state} - {stoich_str}"
                
                break
        
        return extracted

