"""
ChEMBL Drug Database Builder
Downloads approved drugs from ChEMBL and creates local database
"""

from chembl_webresource_client.new_client import new_client
import sqlite3
import pandas as pd
from tqdm import tqdm
import time

class ChEMBLDatabaseBuilder:
    """从ChEMBL下载批准药物并构建本地数据库"""

    def __init__(self, db_file='data/drugbank/chembl_drugs.db'):
        self.db_file = db_file
        self.molecule = new_client.molecule
        self.drug = new_client.drug

    def fetch_approved_drugs(self, limit=5000):
        """
        获取FDA/EMA批准的药物
        ChEMBL包含约2000+批准药物
        """
        print("🔍 Fetching approved drugs from ChEMBL...")

        # 查询已批准的药物（max_phase=4表示已上市）
        approved_drugs = self.molecule.filter(
            max_phase=4  # Phase 4 = Approved/Marketed
        ).only([
            'molecule_chembl_id',
            'pref_name',
            'molecule_properties',
            'molecule_structures',
            'max_phase',
            'first_approval',
            'oral',
            'parenteral',
            'topical',
            'black_box_warning',
            'therapeutic_flag'
        ])[:limit]

        drugs_list = []

        for drug in tqdm(approved_drugs, desc="Processing drugs"):
            try:
                # 基础信息
                chembl_id = drug.get('molecule_chembl_id')
                name = drug.get('pref_name', 'Unknown')

                if not name or name == 'Unknown':
                    continue

                # 性质
                props = drug.get('molecule_properties', {})
                structs = drug.get('molecule_structures', {})

                drug_data = {
                    'chembl_id': chembl_id,
                    'name': name,
                    'molecular_weight': props.get('full_mwt') if props else None,
                    'logp': props.get('alogp') if props else None,
                    'psa': props.get('psa') if props else None,
                    'hba': props.get('hba') if props else None,
                    'hbd': props.get('hbd') if props else None,
                    'num_ro5_violations': props.get('num_ro5_violations') if props else None,
                    'rtb': props.get('rtb') if props else None,
                    'aromatic_rings': props.get('aromatic_rings') if props else None,
                    'smiles': structs.get('canonical_smiles') if structs else None,
                    'inchi_key': structs.get('standard_inchi_key') if structs else None,
                    'first_approval': drug.get('first_approval'),
                    'oral': drug.get('oral', False),
                    'parenteral': drug.get('parenteral', False),
                    'topical': drug.get('topical', False),
                    'black_box': drug.get('black_box_warning', False),
                    'therapeutic': drug.get('therapeutic_flag', False)
                }

                drugs_list.append(drug_data)

            except Exception as e:
                print(f"Error processing {drug.get('pref_name', 'unknown')}: {e}")
                continue

            # Rate limiting
            if len(drugs_list) % 100 == 0:
                time.sleep(0.5)

        print(f"✅ Fetched {len(drugs_list)} approved drugs")
        return pd.DataFrame(drugs_list)

    def predict_bcs_class(self, row):
        """预测BCS分类"""
        try:
            mw = float(row['molecular_weight']) if row['molecular_weight'] else 0
            logp = float(row['logp']) if row['logp'] else 0
            hbd = int(row['hbd']) if row['hbd'] else 0
            psa = float(row['psa']) if row['psa'] else 0

            # 高溶解度
            high_solubility = (mw < 500 and logp < 5 and row['num_ro5_violations'] == 0)

            # 高渗透性
            high_permeability = (0 < logp < 3 and psa < 140 and hbd < 5)

            if high_solubility and high_permeability:
                return "BCS I"
            elif not high_solubility and high_permeability:
                return "BCS II"
            elif high_solubility and not high_permeability:
                return "BCS III"
            else:
                return "BCS IV"
        except:
            return "Unknown"

    def create_database(self, df):
        """创建SQLite数据库"""
        print(f"💾 Creating database: {self.db_file}")

        # 预测BCS分类
        print("🔮 Predicting BCS classifications...")
        df['bcs_class'] = df.apply(self.predict_bcs_class, axis=1)

        # 创建数据库
        conn = sqlite3.connect(self.db_file)

        # 保存到SQLite
        df.to_sql('drugs', conn, if_exists='replace', index=False)

        # 创建索引
        conn.execute('CREATE INDEX IF NOT EXISTS idx_name ON drugs(name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_bcs ON drugs(bcs_class)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_mw ON drugs(molecular_weight)')

        conn.commit()
        conn.close()

        print(f"✅ Database created with {len(df)} drugs")

        # 统计
        print("\n📊 Statistics:")
        print(f"Total drugs: {len(df)}")
        print(f"BCS distribution:")
        print(df['bcs_class'].value_counts())
        print(f"\nOral: {df['oral'].sum()}")
        print(f"Parenteral: {df['parenteral'].sum()}")
        print(f"Black Box Warning: {df['black_box'].sum()}")

    def build(self, limit=5000):
        """构建完整数据库"""
        # 获取数据
        df = self.fetch_approved_drugs(limit=limit)

        # 创建数据库
        self.create_database(df)

        return df


if __name__ == '__main__':
    import os

    # 确保目录存在
    os.makedirs('data/drugbank', exist_ok=True)

    print("🚀 ChEMBL Drug Database Builder")
    print("=" * 50)
    print()

    builder = ChEMBLDatabaseBuilder('data/drugbank/chembl_drugs.db')

    # 构建数据库（获取所有批准药物，最多5000个）
    df = builder.build(limit=5000)

    print()
    print("🎉 Complete!")
    print(f"Database saved to: data/drugbank/chembl_drugs.db")
    print(f"Total drugs: {len(df)}")
