"""
Citation-based LLM Response Generator
Generate Perplexity-style answers with literature citations
"""

from typing import List, Dict, Optional, Tuple
from src.formulation_os.knowledge.pubmed_search import PubMedSearchEngine
import re

class CitationLLM:
    """带引用来源的AI回答生成器"""

    def __init__(self, llm_client, model: str = "gpt-4o"):
        self.llm_client = llm_client
        self.model = model
        self.pubmed = PubMedSearchEngine()

    def answer_with_citations(self, question: str, domain: str = "formulation") -> Dict:
        """
        生成带引用来源的回答

        Args:
            question: 用户问题
            domain: 领域（formulation, drug, technology）

        Returns:
            {
                'answer': 带引用标记的回答文本,
                'citations': 引用文献列表,
                'search_queries': 使用的搜索查询
            }
        """
        # Step 1: 从问题中提取关键词并搜索文献
        search_queries = self._extract_search_queries(question, domain)

        all_papers = []
        for query in search_queries[:2]:  # 限制搜索次数
            papers = self.pubmed.search_literature(query, max_results=5)
            all_papers.extend(papers)

        if not all_papers:
            return {
                'answer': self._generate_fallback_answer(question),
                'citations': [],
                'search_queries': search_queries
            }

        # 去重（基于PMID）
        seen_pmids = set()
        unique_papers = []
        for paper in all_papers:
            if paper['pmid'] not in seen_pmids:
                seen_pmids.add(paper['pmid'])
                unique_papers.append(paper)

        # Step 2: 构建带文献上下文的prompt
        literature_context = self._build_literature_context(unique_papers[:5])

        prompt = f"""You are a pharmaceutical formulation expert. Answer the following question based on the provided scientific literature.

**Question:** {question}

**Scientific Literature:**
{literature_context}

**Instructions:**
1. Provide a comprehensive, evidence-based answer
2. Cite sources using [1], [2], [3] format after relevant statements
3. Synthesize information from multiple papers when possible
4. Be specific about techniques, mechanisms, and outcomes
5. If literature conflicts, mention both perspectives
6. Keep answer clear and professional

**Answer (with citations):**"""

        # Step 3: 调用LLM生成回答
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical formulation scientist providing evidence-based answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            answer = response.choices[0].message.content

            return {
                'answer': answer,
                'citations': unique_papers[:5],
                'search_queries': search_queries
            }

        except Exception as e:
            return {
                'answer': f"Error generating answer: {str(e)}",
                'citations': unique_papers[:5],
                'search_queries': search_queries
            }

    def _extract_search_queries(self, question: str, domain: str) -> List[str]:
        """从问题中提取PubMed搜索查询"""

        # 简单关键词提取
        queries = []

        # 检测药物名称
        drug_pattern = r'(?:ibuprofen|aspirin|paclitaxel|celecoxib|atorvastatin|metformin|carvedilol|fenofibrate|ritonavir|amphotericin)'
        drug_match = re.search(drug_pattern, question.lower())

        # 检测技术/策略
        tech_pattern = r'(?:solid dispersion|nanocrystal|SEDDS|liposome|cyclodextrin|amorphous|ASD|hot melt extrusion|spray drying)'
        tech_match = re.search(tech_pattern, question.lower())

        # 检测BCS分类
        bcs_pattern = r'BCS (?:I|II|III|IV|class|[1-4])'
        bcs_match = re.search(bcs_pattern, question, re.IGNORECASE)

        if drug_match:
            drug = drug_match.group()
            queries.append(f'"{drug}" AND (formulation OR bioavailability OR solubility)')

        if tech_match:
            tech = tech_match.group()
            queries.append(f'"{tech}" AND (formulation OR drug delivery)')

        if bcs_match:
            bcs_class = bcs_match.group()
            queries.append(f'"{bcs_class}" AND (formulation OR solubility enhancement)')

        # 通用制剂查询
        if not queries:
            if 'solubility' in question.lower():
                queries.append('solubility enhancement AND formulation')
            elif 'bioavailability' in question.lower():
                queries.append('oral bioavailability AND formulation')
            else:
                queries.append('pharmaceutical formulation AND drug delivery')

        return queries

    def _build_literature_context(self, papers: List[Dict]) -> str:
        """构建文献上下文"""
        context_parts = []

        for i, paper in enumerate(papers, 1):
            context = f"""[{i}] {paper['title']}
Authors: {paper['authors_full']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {paper['abstract'][:500]}...
PMID: {paper['pmid']}
"""
            context_parts.append(context)

        return '\n\n'.join(context_parts)

    def _generate_fallback_answer(self, question: str) -> str:
        """在没有文献时生成回答"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical formulation expert."},
                    {"role": "user", "content": f"Answer this question based on general pharmaceutical knowledge: {question}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content + "\n\n⚠️ Note: This answer is not based on recent literature search."
        except:
            return "Unable to generate answer. Please try rephrasing your question."
