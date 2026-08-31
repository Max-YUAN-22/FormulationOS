#!/usr/bin/env python3
"""
DrugBank XML Parser
解析DrugBank完整数据库XML文件并导入SQLite
"""

import xml.etree.ElementTree as ET
import sqlite3
from pathlib import Path
import sys

class DrugBankParser:
    """DrugBank XML解析器"""

    # DrugBank XML命名空间
    NS = {'db': 'http://www.drugbank.ca'}

    def __init__(self, xml_file, db_file):
        self.xml_file = xml_file
        self.db_file = db_file
        self.conn = None

    def create_tables(self):
        """创建SQLite数据库表"""
        self.conn = sqlite3.connect(self.db_file)
        cursor = self.conn.cursor()

        # 药物主表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drugs (
            drugbank_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            cas_number TEXT,
            unii TEXT,
            state TEXT,
            type TEXT,

            -- Chemical properties
            smiles TEXT,
            inchi TEXT,
            inchikey TEXT,
            molecular_formula TEXT,
            molecular_weight REAL,

            -- Calculated properties
            logp REAL,
            logs REAL,
            pka_strongest_acidic REAL,
            pka_strongest_basic REAL,
            polar_surface_area REAL,
            rotatable_bond_count INTEGER,
            h_bond_acceptor_count INTEGER,
            h_bond_donor_count INTEGER,

            -- Pharmaceutical info
            indication TEXT,
            pharmacodynamics TEXT,
            mechanism_of_action TEXT,
            toxicity TEXT,
            metabolism TEXT,
            absorption TEXT,
            half_life TEXT,
            protein_binding TEXT,

            -- Classification
            classification_description TEXT,
            classification_kingdom TEXT,
            classification_superclass TEXT,
            classification_class TEXT,
            classification_subclass TEXT,

            -- BCS prediction
            bcs_class TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_name ON drugs(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_cas ON drugs(cas_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_bcs ON drugs(bcs_class)')

        self.conn.commit()
        print("✅ Database tables created")

    def get_text(self, element, path):
        """安全获取XML元素文本"""
        el = element.find(path, self.NS)
        return el.text if el is not None else None

    def get_property_value(self, drug_element, property_kind):
        """获取calculated-properties中的特定属性值"""
        props = drug_element.findall('.//db:calculated-properties/db:property', self.NS)
        for prop in props:
            kind = self.get_text(prop, 'db:kind')
            if kind == property_kind:
                return self.get_text(prop, 'db:value')
        return None

    def predict_bcs_class(self, mw, logp, logs, hbd, psa):
        """预测BCS分类"""
        try:
            mw = float(mw) if mw else 0
            logp = float(logp) if logp else 0
            logs = float(logs) if logs else 0
            hbd = int(hbd) if hbd else 0
            psa = float(psa) if psa else 0

            # 高溶解度预测
            high_solubility = logs > -4 or (mw < 500 and logp < 5)

            # 高渗透性预测
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
            return None

    def parse_drug(self, drug_element):
        """解析单个药物条目"""
        drugbank_id = self.get_text(drug_element, './/db:drugbank-id[@primary="true"]')

        if not drugbank_id:
            return None

        # Basic info
        name = self.get_text(drug_element, 'db:name')
        description = self.get_text(drug_element, 'db:description')
        cas_number = self.get_text(drug_element, 'db:cas-number')
        unii = self.get_text(drug_element, 'db:unii')
        state = self.get_text(drug_element, 'db:state')
        drug_type = drug_element.get('type')

        # Chemical properties
        smiles = self.get_property_value(drug_element, 'SMILES')
        inchi = self.get_property_value(drug_element, 'InChI')
        inchikey = self.get_property_value(drug_element, 'InChIKey')
        molecular_formula = self.get_property_value(drug_element, 'Molecular Formula')
        molecular_weight = self.get_property_value(drug_element, 'Molecular Weight')

        # Calculated properties
        logp = self.get_property_value(drug_element, 'logP')
        logs = self.get_property_value(drug_element, 'logS')
        pka_acidic = self.get_property_value(drug_element, 'pKa (strongest acidic)')
        pka_basic = self.get_property_value(drug_element, 'pKa (strongest basic)')
        psa = self.get_property_value(drug_element, 'Polar Surface Area (PSA)')
        hbd = self.get_property_value(drug_element, 'H Bond Donor Count')
        hba = self.get_property_value(drug_element, 'H Bond Acceptor Count')
        rotatable_bonds = self.get_property_value(drug_element, 'Rotatable Bond Count')

        # Pharmaceutical info
        indication = self.get_text(drug_element, 'db:indication')
        pharmacodynamics = self.get_text(drug_element, 'db:pharmacodynamics')
        mechanism = self.get_text(drug_element, 'db:mechanism-of-action')
        toxicity = self.get_text(drug_element, 'db:toxicity')
        metabolism = self.get_text(drug_element, 'db:metabolism')
        absorption = self.get_text(drug_element, 'db:absorption')
        half_life = self.get_text(drug_element, 'db:half-life')
        protein_binding = self.get_text(drug_element, 'db:protein-binding')

        # Classification
        classification = drug_element.find('db:classification', self.NS)
        class_desc = None
        class_kingdom = None
        class_superclass = None
        class_class = None
        class_subclass = None

        if classification is not None:
            class_desc = self.get_text(classification, 'db:description')
            class_kingdom = self.get_text(classification, 'db:kingdom')
            class_superclass = self.get_text(classification, 'db:superclass')
            class_class = self.get_text(classification, 'db:class')
            class_subclass = self.get_text(classification, 'db:subclass')

        # Predict BCS class
        bcs_class = self.predict_bcs_class(molecular_weight, logp, logs, hbd, psa)

        return (
            drugbank_id, name, description, cas_number, unii, state, drug_type,
            smiles, inchi, inchikey, molecular_formula, molecular_weight,
            logp, logs, pka_acidic, pka_basic, psa,
            rotatable_bonds, hba, hbd,
            indication, pharmacodynamics, mechanism, toxicity,
            metabolism, absorption, half_life, protein_binding,
            class_desc, class_kingdom, class_superclass, class_class, class_subclass,
            bcs_class
        )

    def parse_all(self):
        """解析整个XML文件"""
        print(f"📖 Parsing {self.xml_file}...")
        print("⏳ This may take 5-10 minutes...")

        context = ET.iterparse(self.xml_file, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)

        drug_count = 0
        cursor = self.conn.cursor()

        for event, elem in context:
            if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
                drug_data = self.parse_drug(elem)

                if drug_data:
                    cursor.execute('''
                    INSERT OR REPLACE INTO drugs VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, CURRENT_TIMESTAMP
                    )
                    ''', drug_data)

                    drug_count += 1
                    if drug_count % 500 == 0:
                        print(f"  ✓ Processed {drug_count} drugs...")
                        self.conn.commit()

                elem.clear()
                root.clear()

        self.conn.commit()
        print(f"✅ Successfully parsed {drug_count} drugs")
        return drug_count

    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    import argparse
    import zipfile

    ap = argparse.ArgumentParser(description="Parse DrugBank full-database XML (or .zip) into SQLite")
    ap.add_argument(
        "input",
        nargs="?",
        default="/Users/Apple/FormulationOS/data/drugbank/full_database.xml",
        help="Path to 'full database.xml' or the DrugBank .xml.zip (streamed, no extraction needed)",
    )
    ap.add_argument(
        "-o", "--output",
        default="/Users/Apple/FormulationOS/data/drugbank/drugbank.db",
        help="Output SQLite path (default: data/drugbank/drugbank.db, git-ignored)",
    )
    args = ap.parse_args()

    print("🚀 DrugBank XML Parser")
    print(f"📂 Input:  {args.input}")
    print(f"💾 Output: {args.output}")
    print()

    if not Path(args.input).exists():
        print(f"❌ Error: input not found at {args.input}")
        print("📥 Point this at your DrugBank download, e.g.:")
        print('   python scripts/parse_drugbank_xml.py "/Users/Apple/Desktop/Year 4/FYP 欧阳/drugbank_all_full_database（5-1-19版本）.xml.zip"')
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Stream the XML directly — from a .zip inner file when given a zip, so the
    # 2.57 GB XML never has to be extracted to disk.
    xml_source = args.input
    zf = None
    if zipfile.is_zipfile(args.input):
        zf = zipfile.ZipFile(args.input)
        inner = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
        if inner is None:
            print("❌ No .xml inside the zip")
            sys.exit(1)
        print(f"📦 Streaming '{inner}' from zip (no extraction)")
        xml_source = zf.open(inner)

    parser = DrugBankParser(xml_source, args.output)
    parser.create_tables()
    total_drugs = parser.parse_all()
    parser.close()
    if zf is not None:
        zf.close()

    print()
    print(f"🎉 Complete! {total_drugs} drugs imported into {args.output}")
    print()
    print("Next step: build the local drug-intelligence DB including DrugBank:")
    print("   python scripts/build_drug_intelligence.py --profile local")
