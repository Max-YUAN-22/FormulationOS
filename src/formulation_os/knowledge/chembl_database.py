"""
ChEMBL Drug Database Interface
Access to 4,000+ FDA/EMA approved drugs from ChEMBL
"""

import sqlite3
import pandas as pd
from typing import Optional, List, Dict

class ChEMBLDrugDatabase:
    """ChEMBL批准药物数据库接口"""

    def __init__(self, db_path='data/drugbank/chembl_drugs.db'):
        self.db_path = db_path

    def get_all_drugs(self) -> pd.DataFrame:
        """获取所有药物"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM drugs", conn)
        conn.close()

        # Convert numeric columns to proper types
        numeric_cols = ['molecular_weight', 'logp', 'psa', 'hba', 'hbd', 'num_ro5_violations']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def search_drugs(self, query: str, limit: int = 50) -> pd.DataFrame:
        """搜索药物"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            """
            SELECT * FROM drugs
            WHERE name LIKE ? OR chembl_id LIKE ?
            LIMIT ?
            """,
            conn,
            params=(f'%{query}%', f'%{query}%', limit)
        )
        conn.close()

        # Convert numeric columns to proper types
        numeric_cols = ['molecular_weight', 'logp', 'psa', 'hba', 'hbd', 'num_ro5_violations']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_drugs_by_bcs(self, bcs_class: str, limit: int = 100) -> pd.DataFrame:
        """按BCS分类获取药物"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            "SELECT * FROM drugs WHERE bcs_class = ? LIMIT ?",
            conn,
            params=(bcs_class, limit)
        )
        conn.close()

        # Convert numeric columns to proper types
        numeric_cols = ['molecular_weight', 'logp', 'psa', 'hba', 'hbd', 'num_ro5_violations']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_drug_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取单个药物"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drugs WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总数
        cursor.execute("SELECT COUNT(*) FROM drugs")
        total = cursor.fetchone()[0]

        # BCS分布
        cursor.execute("""
            SELECT bcs_class, COUNT(*) as count
            FROM drugs
            GROUP BY bcs_class
        """)
        bcs_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # 平均分子量
        cursor.execute("SELECT AVG(molecular_weight) FROM drugs WHERE molecular_weight IS NOT NULL")
        avg_mw = cursor.fetchone()[0]

        # 口服药物数
        cursor.execute("SELECT COUNT(*) FROM drugs WHERE oral = 1")
        oral_count = cursor.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'bcs_distribution': bcs_dist,
            'avg_molecular_weight': avg_mw,
            'oral_drugs': oral_count
        }

    def filter_drugs(self,
                     bcs_classes: List[str] = None,
                     oral_only: bool = False,
                     mw_range: tuple = None,
                     limit: int = 1000) -> pd.DataFrame:
        """高级筛选"""
        conditions = []
        params = []

        if bcs_classes:
            placeholders = ','.join(['?' for _ in bcs_classes])
            conditions.append(f"bcs_class IN ({placeholders})")
            params.extend(bcs_classes)

        if oral_only:
            conditions.append("oral = 1")

        if mw_range:
            conditions.append("molecular_weight BETWEEN ? AND ?")
            params.extend(mw_range)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            f"SELECT * FROM drugs WHERE {where_clause} LIMIT ?",
            conn,
            params=params + [limit]
        )
        conn.close()

        # Convert numeric columns to proper types
        numeric_cols = ['molecular_weight', 'logp', 'psa', 'hba', 'hbd', 'num_ro5_violations']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
