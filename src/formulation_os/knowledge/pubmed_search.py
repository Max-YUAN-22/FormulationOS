"""
PubMed Literature Search Integration
Real-time access to biomedical literature for formulation intelligence
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import time
from datetime import datetime

class PubMedSearchEngine:
    """PubMed文献检索引擎"""

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.db = "pubmed"
        # NCBI推荐：添加email和tool参数以获得更好的服务
        self.email = "research@formulationos.ai"
        self.tool = "FormulationOS"

    def search_literature(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        搜索PubMed文献

        Args:
            query: 搜索关键词
            max_results: 最大返回结果数

        Returns:
            文献列表，每个文献包含标题、摘要、作者、期刊等信息
        """
        # Step 1: Search - 获取PMID列表
        search_url = f"{self.base_url}esearch.fcgi"
        search_params = {
            'db': self.db,
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email,
            'tool': self.tool,
            'sort': 'relevance'  # 按相关性排序
        }

        try:
            response = requests.get(search_url, params=search_params, timeout=10)
            response.raise_for_status()
            search_results = response.json()

            pmid_list = search_results.get('esearchresult', {}).get('idlist', [])

            if not pmid_list:
                return []

            # Step 2: Fetch - 获取详细信息
            time.sleep(0.34)  # NCBI要求：每秒不超过3次请求

            fetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                'db': self.db,
                'id': ','.join(pmid_list),
                'retmode': 'xml',
                'email': self.email,
                'tool': self.tool
            }

            response = requests.get(fetch_url, params=fetch_params, timeout=15)
            response.raise_for_status()

            # 解析XML
            articles = self._parse_pubmed_xml(response.text)
            return articles

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """解析PubMed XML响应"""
        articles = []

        try:
            root = ET.fromstring(xml_text)

            for article_elem in root.findall('.//PubmedArticle'):
                article = {}

                # PMID
                pmid_elem = article_elem.find('.//PMID')
                article['pmid'] = pmid_elem.text if pmid_elem is not None else 'N/A'

                # 标题
                title_elem = article_elem.find('.//ArticleTitle')
                article['title'] = title_elem.text if title_elem is not None else 'No title'

                # 摘要
                abstract_elems = article_elem.findall('.//AbstractText')
                if abstract_elems:
                    abstract_parts = []
                    for abs_elem in abstract_elems:
                        label = abs_elem.get('Label', '')
                        text = abs_elem.text or ''
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    article['abstract'] = ' '.join(abstract_parts)
                else:
                    article['abstract'] = 'No abstract available'

                # 作者
                authors = []
                for author in article_elem.findall('.//Author'):
                    lastname = author.find('LastName')
                    forename = author.find('ForeName')
                    if lastname is not None and forename is not None:
                        authors.append(f"{forename.text} {lastname.text}")
                    elif lastname is not None:
                        authors.append(lastname.text)

                article['authors'] = authors[:3]  # 只取前3位作者
                article['authors_full'] = ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else '')

                # 期刊
                journal_elem = article_elem.find('.//Journal/Title')
                article['journal'] = journal_elem.text if journal_elem is not None else 'Unknown'

                # 发表年份
                year_elem = article_elem.find('.//PubDate/Year')
                article['year'] = year_elem.text if year_elem is not None else 'N/A'

                # DOI
                doi_elem = article_elem.find('.//ArticleId[@IdType="doi"]')
                article['doi'] = doi_elem.text if doi_elem is not None else None

                # PubMed链接
                article['pubmed_url'] = f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/"

                articles.append(article)

        except ET.ParseError as e:
            print(f"XML parsing error: {e}")

        return articles

    def search_formulation_trends(self, drug_class: str = "BCS II") -> List[Dict]:
        """搜索制剂趋势"""
        query = f'"{drug_class}" AND (formulation OR "solid dispersion" OR nanocrystal) AND (clinical trial OR bioavailability)'
        return self.search_literature(query, max_results=5)

    def search_drug_formulation(self, drug_name: str) -> List[Dict]:
        """搜索特定药物的制剂研究"""
        query = f'"{drug_name}" AND (formulation OR "drug delivery" OR bioavailability OR solubility)'
        return self.search_literature(query, max_results=5)

    def search_technology(self, technology: str) -> List[Dict]:
        """搜索特定技术的文献"""
        tech_queries = {
            'ASD': '"amorphous solid dispersion" OR "solid dispersion"',
            'Nanocrystal': 'nanocrystal OR nanosuspension',
            'SEDDS': '"self-emulsifying drug delivery" OR SEDDS OR SNEDDS',
            'Liposome': 'liposome OR liposomal',
            'Cyclodextrin': 'cyclodextrin OR "inclusion complex"'
        }

        query = tech_queries.get(technology, technology)
        query += ' AND (formulation OR bioavailability)'

        return self.search_literature(query, max_results=8)
