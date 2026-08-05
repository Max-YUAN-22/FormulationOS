# 自建DrugBank MCP服务器 - 完整实施指南

## 目标
下载完整DrugBank数据，解析后构建自己的MCP服务器，供FormulationOS和其他AI工具使用。

## Phase 1: 下载DrugBank数据（现在就做）

### 步骤1：登录并下载

1. **登录DrugBank账号**
   - 访问：https://go.drugbank.com/
   - 使用你刚注册的账号登录

2. **进入下载页面**
   - 访问：https://go.drugbank.com/releases/latest
   - 或在顶部导航 → "Downloads"

3. **选择下载内容**（推荐下载以下文件）：

   **必需文件：**
   - ✅ **Full Database** - `drugbank_all_full_database.xml.zip` (最全面，~200MB)
     - 包含所有药物的完整信息
     - XML格式，包含结构化数据
   
   **可选补充文件：**
   - 📊 **Structures** - `structures.sdf.zip` (化学结构文件)
   - 📊 **All Drugbank Vocabulary** - CSV格式的结构化数据
   - 📊 **Drug Product Data** - 实际产品信息

4. **下载到项目目录**
   ```bash
   mkdir -p /Users/Apple/FormulationOS/data/drugbank
   # 下载后移动文件到这个目录
   ```

5. **解压文件**
   ```bash
   cd /Users/Apple/FormulationOS/data/drugbank
   unzip drugbank_all_full_database.xml.zip
   # 得到 full_database.xml (约1GB解压后)
   ```

## Phase 2: 解析DrugBank XML数据

### 数据解析脚本

```python
# scripts/parse_drugbank_xml.py

import xml.etree.ElementTree as ET
import sqlite3
import json
from tqdm import tqdm
from pathlib import Path

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
            monoisotopic_weight REAL,
            
            -- Calculated properties
            logp REAL,
            logs REAL,
            logd REAL,
            pka_strongest_acidic REAL,
            pka_strongest_basic REAL,
            polar_surface_area REAL,
            refractivity REAL,
            polarizability REAL,
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
            route_of_elimination TEXT,
            volume_of_distribution TEXT,
            clearance TEXT,
            
            -- Classification
            classification_description TEXT,
            classification_direct_parent TEXT,
            classification_kingdom TEXT,
            classification_superclass TEXT,
            classification_class TEXT,
            classification_subclass TEXT,
            
            -- BCS prediction (will be calculated)
            bcs_class TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 药物分类表（多对多）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT,
            category TEXT,
            mesh_id TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        ''')
        
        # 药物产品表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT,
            name TEXT,
            labeller TEXT,
            ndc_id TEXT,
            ndc_product_code TEXT,
            dpd_id TEXT,
            started_marketing_on TEXT,
            ended_marketing_on TEXT,
            dosage_form TEXT,
            strength TEXT,
            route TEXT,
            fda_application_number TEXT,
            generic INTEGER,
            over_the_counter INTEGER,
            approved INTEGER,
            country TEXT,
            source TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        ''')
        
        # 药物靶点表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT,
            target_id TEXT,
            name TEXT,
            organism TEXT,
            known_action TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        ''')
        
        # 药物相互作用表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drugbank_id TEXT,
            interacting_drug_id TEXT,
            description TEXT,
            FOREIGN KEY (drugbank_id) REFERENCES drugs(drugbank_id)
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_name ON drugs(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_cas ON drugs(cas_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_drug_bcs ON drugs(bcs_class)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category_drug ON drug_categories(drugbank_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_drug ON drug_products(drugbank_id)')
        
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
            
            # 高溶解度预测：LogS > -4 或 MW<500且LogP<5
            high_solubility = logs > -4 or (mw < 500 and logp < 5)
            
            # 高渗透性预测：0<LogP<3, PSA<140, HBD<5
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
        # Primary ID
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
        class_parent = None
        class_kingdom = None
        class_superclass = None
        class_class = None
        class_subclass = None
        
        if classification is not None:
            class_desc = self.get_text(classification, 'db:description')
            class_parent = self.get_text(classification, 'db:direct-parent')
            class_kingdom = self.get_text(classification, 'db:kingdom')
            class_superclass = self.get_text(classification, 'db:superclass')
            class_class = self.get_text(classification, 'db:class')
            class_subclass = self.get_text(classification, 'db:subclass')
        
        # Predict BCS class
        bcs_class = self.predict_bcs_class(molecular_weight, logp, logs, hbd, psa)
        
        return {
            'drugbank_id': drugbank_id,
            'name': name,
            'description': description,
            'cas_number': cas_number,
            'unii': unii,
            'state': state,
            'type': drug_type,
            'smiles': smiles,
            'inchi': inchi,
            'inchikey': inchikey,
            'molecular_formula': molecular_formula,
            'molecular_weight': molecular_weight,
            'logp': logp,
            'logs': logs,
            'pka_strongest_acidic': pka_acidic,
            'pka_strongest_basic': pka_basic,
            'polar_surface_area': psa,
            'h_bond_donor_count': hbd,
            'h_bond_acceptor_count': hba,
            'rotatable_bond_count': rotatable_bonds,
            'indication': indication,
            'pharmacodynamics': pharmacodynamics,
            'mechanism_of_action': mechanism,
            'toxicity': toxicity,
            'metabolism': metabolism,
            'absorption': absorption,
            'half_life': half_life,
            'protein_binding': protein_binding,
            'classification_description': class_desc,
            'classification_direct_parent': class_parent,
            'classification_kingdom': class_kingdom,
            'classification_superclass': class_superclass,
            'classification_class': class_class,
            'classification_subclass': class_subclass,
            'bcs_class': bcs_class
        }
    
    def parse_all(self):
        """解析整个XML文件"""
        print(f"📖 Parsing {self.xml_file}...")
        
        # 使用iterparse避免一次性加载整个文件到内存
        context = ET.iterparse(self.xml_file, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        drug_count = 0
        cursor = self.conn.cursor()
        
        for event, elem in context:
            if event == 'end' and elem.tag == '{http://www.drugbank.ca}drug':
                drug_data = self.parse_drug(elem)
                
                if drug_data:
                    # 插入到数据库
                    cursor.execute('''
                    INSERT OR REPLACE INTO drugs VALUES (
                        :drugbank_id, :name, :description, :cas_number, :unii, :state, :type,
                        :smiles, :inchi, :inchikey, :molecular_formula, :molecular_weight, NULL,
                        :logp, :logs, NULL, :pka_strongest_acidic, :pka_strongest_basic,
                        :polar_surface_area, NULL, NULL,
                        :rotatable_bond_count, :h_bond_acceptor_count, :h_bond_donor_count,
                        :indication, :pharmacodynamics, :mechanism_of_action, :toxicity,
                        :metabolism, :absorption, :half_life, :protein_binding,
                        NULL, NULL, NULL,
                        :classification_description, :classification_direct_parent,
                        :classification_kingdom, :classification_superclass,
                        :classification_class, :classification_subclass,
                        :bcs_class, CURRENT_TIMESTAMP
                    )
                    ''', drug_data)
                    
                    drug_count += 1
                    if drug_count % 100 == 0:
                        print(f"  Processed {drug_count} drugs...")
                        self.conn.commit()
                
                # 清理已处理的元素以释放内存
                elem.clear()
                root.clear()
        
        self.conn.commit()
        print(f"✅ Successfully parsed {drug_count} drugs")
        return drug_count
    
    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    import sys
    
    xml_file = '/Users/Apple/FormulationOS/data/drugbank/full_database.xml'
    db_file = '/Users/Apple/FormulationOS/data/drugbank/drugbank.db'
    
    print("🚀 DrugBank XML Parser")
    print(f"📂 Input: {xml_file}")
    print(f"💾 Output: {db_file}")
    print()
    
    parser = DrugBankParser(xml_file, db_file)
    parser.create_tables()
    total_drugs = parser.parse_all()
    parser.close()
    
    print()
    print(f"🎉 Complete! {total_drugs} drugs imported into {db_file}")
```

## Phase 3: 构建MCP服务器

### MCP服务器实现

```python
# src/formulation_os/mcp/drugbank_mcp_server.py

"""
DrugBank MCP Server
基于Model Context Protocol标准实现的DrugBank数据服务器
"""

import json
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path

class DrugBankMCPServer:
    """DrugBank MCP服务器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 返回字典格式
    
    def search_drugs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索药物
        支持按名称、CAS号、DrugBank ID搜索
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            drugbank_id, name, description,
            molecular_weight, logp, logs,
            bcs_class, indication
        FROM drugs
        WHERE 
            name LIKE ? OR
            drugbank_id LIKE ? OR
            cas_number LIKE ?
        LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_drug_detail(self, drugbank_id: str) -> Optional[Dict]:
        """获取药物详细信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM drugs WHERE drugbank_id = ?', (drugbank_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_drugs_by_bcs_class(self, bcs_class: str, limit: int = 50) -> List[Dict]:
        """按BCS分类获取药物列表"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT drugbank_id, name, molecular_weight, logp, logs, indication
        FROM drugs
        WHERE bcs_class = ?
        LIMIT ?
        ''', (bcs_class, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # 总药物数
        cursor.execute('SELECT COUNT(*) FROM drugs')
        stats['total_drugs'] = cursor.fetchone()[0]
        
        # BCS分类统计
        cursor.execute('''
        SELECT bcs_class, COUNT(*) as count
        FROM drugs
        WHERE bcs_class IS NOT NULL
        GROUP BY bcs_class
        ''')
        stats['bcs_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 药物类型统计
        cursor.execute('''
        SELECT type, COUNT(*) as count
        FROM drugs
        GROUP BY type
        ''')
        stats['type_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats
    
    # MCP Protocol Methods
    def handle_request(self, request: Dict) -> Dict:
        """
        处理MCP请求
        MCP请求格式：
        {
            "method": "search_drugs" | "get_drug_detail" | ...,
            "params": {...}
        }
        """
        method = request.get('method')
        params = request.get('params', {})
        
        if method == 'search_drugs':
            query = params.get('query', '')
            limit = params.get('limit', 10)
            results = self.search_drugs(query, limit)
            return {'status': 'success', 'data': results}
        
        elif method == 'get_drug_detail':
            drugbank_id = params.get('drugbank_id')
            result = self.get_drug_detail(drugbank_id)
            if result:
                return {'status': 'success', 'data': result}
            else:
                return {'status': 'error', 'message': 'Drug not found'}
        
        elif method == 'get_drugs_by_bcs_class':
            bcs_class = params.get('bcs_class')
            limit = params.get('limit', 50)
            results = self.get_drugs_by_bcs_class(bcs_class, limit)
            return {'status': 'success', 'data': results}
        
        elif method == 'get_statistics':
            stats = self.get_statistics()
            return {'status': 'success', 'data': stats}
        
        else:
            return {'status': 'error', 'message': f'Unknown method: {method}'}
    
    def close(self):
        self.conn.close()


# Flask API wrapper (可选 - 如果想通过HTTP访问)
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 初始化MCP服务器
mcp_server = DrugBankMCPServer('/Users/Apple/FormulationOS/data/drugbank/drugbank.db')

@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """MCP API endpoint"""
    request_data = request.get_json()
    response = mcp_server.handle_request(request_data)
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'service': 'DrugBank MCP Server'})

if __name__ == '__main__':
    print("🚀 Starting DrugBank MCP Server...")
    print("📍 Endpoint: http://localhost:5000/mcp")
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Phase 4: 集成到FormulationOS

```python
# 在 FormulationOS_Enterprise.py 中集成

from src.formulation_os.mcp.drugbank_mcp_server import DrugBankMCPServer

# 初始化MCP客户端
if "drugbank_mcp" not in st.session_state:
    st.session_state.drugbank_mcp = DrugBankMCPServer(
        '/Users/Apple/FormulationOS/data/drugbank/drugbank.db'
    )

# 在Knowledge Base -> Drug Database tab使用
with tab1:
    st.markdown("### 🔍 DrugBank Search (13,000+ Drugs)")
    
    search_query = st.text_input("Search drugs by name, CAS, or DrugBank ID")
    
    if search_query:
        results = st.session_state.drugbank_mcp.search_drugs(search_query, limit=20)
        
        if results:
            st.success(f"Found {len(results)} results")
            
            for drug in results:
                with st.expander(f"💊 {drug['name']} ({drug['drugbank_id']})"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("MW", f"{drug.get('molecular_weight', 'N/A')}")
                    with col2:
                        st.metric("LogP", f"{drug.get('logp', 'N/A')}")
                    with col3:
                        st.metric("LogS", f"{drug.get('logs', 'N/A')}")
                    with col4:
                        if drug.get('bcs_class'):
                            st.info(f"**{drug['bcs_class']}**")
                    
                    if drug.get('indication'):
                        st.markdown(f"**Indication:** {drug['indication'][:300]}...")
                    
                    if st.button("View Full Details", key=f"detail_{drug['drugbank_id']}"):
                        detail = st.session_state.drugbank_mcp.get_drug_detail(drug['drugbank_id'])
                        st.json(detail)
```

## 执行清单

### 现在立即执行：

1. **下载数据** (5分钟)
   ```bash
   # 登录 https://go.drugbank.com/
   # Downloads → Full Database → drugbank_all_full_database.xml.zip
   # 下载到 /Users/Apple/FormulationOS/data/drugbank/
   ```

2. **解压文件** (1分钟)
   ```bash
   cd /Users/Apple/FormulationOS/data/drugbank
   unzip drugbank_all_full_database.xml.zip
   ```

告诉我你下载完成了，我立即帮你运行解析脚本！📥
