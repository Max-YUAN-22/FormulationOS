"""
Drug Search Module
Integrates PubChem API for real-time drug property queries
with BCS classification prediction
"""

import requests
from typing import Optional, Dict, List
import sqlite3
from pathlib import Path


class DrugSearchEngine:
    """药物搜索引擎 - PubChem API + BCS预测"""

    def __init__(self, cache_db: str = None):
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.cache_db = cache_db or "formulation_knowledge.db"
        self._init_cache()

    def _init_cache(self):
        """初始化缓存数据库"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_cache (
            name TEXT PRIMARY KEY,
            cid INTEGER,
            molecular_weight REAL,
            logp REAL,
            hbd INTEGER,
            hba INTEGER,
            tpsa REAL,
            rotatable_bonds INTEGER,
            smiles TEXT,
            iupac_name TEXT,
            bcs_class TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()

    def search_drug(self, drug_name: str) -> Optional[Dict]:
        """
        搜索药物信息
        优先从缓存读取，缓存未命中则查询PubChem
        """
        # 1. 检查缓存
        cached = self._get_from_cache(drug_name)
        if cached:
            cached['source'] = 'Cache'
            return cached

        # 2. 查询PubChem
        pubchem_data = self._query_pubchem(drug_name)
        if pubchem_data:
            # 预测BCS分类
            pubchem_data['bcs_class'] = self._predict_bcs_class(pubchem_data)
            # 保存到缓存
            self._save_to_cache(drug_name, pubchem_data)
            pubchem_data['source'] = 'PubChem'
            return pubchem_data

        return None

    def _query_pubchem(self, drug_name: str) -> Optional[Dict]:
        """从PubChem查询药物基础性质"""
        properties = [
            'MolecularWeight',
            'XLogP',
            'HBondDonorCount',
            'HBondAcceptorCount',
            'TPSA',
            'RotatableBondCount',
            'IUPACName',
            'CanonicalSMILES'
        ]

        url = f"{self.pubchem_base}/compound/name/{drug_name}/property/{','.join(properties)}/JSON"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()['PropertyTable']['Properties'][0]

                return {
                    'name': drug_name,
                    'cid': data.get('CID'),
                    'molecular_weight': data.get('MolecularWeight'),
                    'logp': data.get('XLogP'),
                    'hbd': data.get('HBondDonorCount'),
                    'hba': data.get('HBondAcceptorCount'),
                    'tpsa': data.get('TPSA'),
                    'rotatable_bonds': data.get('RotatableBondCount'),
                    'smiles': data.get('CanonicalSMILES'),
                    'iupac_name': data.get('IUPACName')
                }
        except Exception as e:
            print(f"PubChem query failed for {drug_name}: {e}")
            return None

    def _predict_bcs_class(self, drug_data: Dict) -> str:
        """
        基于物化性质预测BCS分类
        参考FDA BCS指南和Lipinski规则
        """
        # Convert to float/int (PubChem may return strings)
        try:
            mw = float(drug_data.get('molecular_weight', 0)) if drug_data.get('molecular_weight') else 0
            logp = float(drug_data.get('logp', 0)) if drug_data.get('logp') else 0
            hbd = int(drug_data.get('hbd', 0)) if drug_data.get('hbd') else 0
            hba = int(drug_data.get('hba', 0)) if drug_data.get('hba') else 0
            tpsa = float(drug_data.get('tpsa', 0)) if drug_data.get('tpsa') else 0
        except (ValueError, TypeError):
            return "Unknown"

        # 高溶解度预测
        # Rule: MW<500, LogP<5, 符合Lipinski规则倾向高溶解度
        high_solubility_score = 0
        if mw < 500:
            high_solubility_score += 1
        if logp < 5:
            high_solubility_score += 1
        if logp < 3:  # 更保守的溶解度标准
            high_solubility_score += 1

        high_solubility = high_solubility_score >= 2

        # 高渗透性预测
        # Rule: 0<LogP<3, TPSA<140, HBD<5
        high_permeability_score = 0
        if 0 < logp < 3:
            high_permeability_score += 1
        if tpsa < 140:
            high_permeability_score += 1
        if hbd < 5:
            high_permeability_score += 1

        high_permeability = high_permeability_score >= 2

        # BCS分类
        if high_solubility and high_permeability:
            return "BCS I"
        elif not high_solubility and high_permeability:
            return "BCS II"
        elif high_solubility and not high_permeability:
            return "BCS III"
        else:
            return "BCS IV"

    def get_formulation_recommendations(self, drug_data: Dict) -> List[str]:
        """根据BCS分类推荐制剂策略"""
        bcs_class = drug_data.get('bcs_class')
        mw = drug_data.get('molecular_weight', 0)
        logp = drug_data.get('logp', 0)

        recommendations = []

        if bcs_class == "BCS I":
            recommendations = [
                "✅ Immediate-release tablets or capsules",
                "✅ Standard formulation approaches",
                "ℹ️ Focus on stability and content uniformity",
                "ℹ️ May consider modified-release for PK optimization"
            ]

        elif bcs_class == "BCS II":
            recommendations = [
                "🎯 Amorphous Solid Dispersion (ASD) - polymer carriers",
                "🎯 Nanocrystal technology - reduce particle size",
                "🎯 Lipid-based formulations (SEDDS) - if LogP>4",
                "🎯 Cyclodextrin complexation - if MW<400 and dose<200mg"
            ]

            if mw > 400:
                recommendations.append("⚠️ High MW: Prefer ASD over cyclodextrin")
            if logp > 4:
                recommendations.append("💡 High LogP: Consider lipid-based systems")

        elif bcs_class == "BCS III":
            recommendations = [
                "🔧 Permeation enhancers (surfactants, fatty acids)",
                "🔧 Phospholipid complex - improve membrane interaction",
                "🔧 Nanocarriers - facilitate transport",
                "⚠️ Limited formulation solutions - permeability is molecular property",
                "💡 Consider prodrug approach if feasible"
            ]

        elif bcs_class == "BCS IV":
            recommendations = [
                "🔴 Most challenging class - dual barriers",
                "🎯 Combination approaches: Nanocrystal + Permeation enhancer",
                "🎯 Lipid-based (SEDDS/SNEDDS) - address both issues",
                "🎯 Phospholipid complex - dual benefit",
                "⚠️ Consider alternative route (IV, inhalation)",
                "💡 High development cost and risk"
            ]

        return recommendations

    def _get_from_cache(self, drug_name: str) -> Optional[Dict]:
        """从本地缓存获取"""
        try:
            conn = sqlite3.connect(self.cache_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM drug_cache WHERE LOWER(name) = LOWER(?)', (drug_name,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
        except:
            pass
        return None

    def _save_to_cache(self, drug_name: str, data: Dict):
        """保存到本地缓存"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO drug_cache
            (name, cid, molecular_weight, logp, hbd, hba, tpsa, rotatable_bonds, smiles, iupac_name, bcs_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                drug_name,
                data.get('cid'),
                data.get('molecular_weight'),
                data.get('logp'),
                data.get('hbd'),
                data.get('hba'),
                data.get('tpsa'),
                data.get('rotatable_bonds'),
                data.get('smiles'),
                data.get('iupac_name'),
                data.get('bcs_class')
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cache save failed: {e}")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM drug_cache')
            total = cursor.fetchone()[0]

            cursor.execute('''
            SELECT bcs_class, COUNT(*)
            FROM drug_cache
            WHERE bcs_class IS NOT NULL
            GROUP BY bcs_class
            ''')
            bcs_dist = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                'total_cached': total,
                'bcs_distribution': bcs_dist
            }
        except:
            return {'total_cached': 0, 'bcs_distribution': {}}
