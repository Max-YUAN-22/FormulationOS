# DrugBank Integration Plan for FormulationOS

## 目标
将DrugBank完整数据集成到Knowledge Base的Drug Database部分，提供详细的药物信息查询功能。

## DrugBank数据访问方案

### 方案1：DrugBank官方数据（推荐）
**来源：** https://go.drugbank.com/releases/latest

**数据格式：**
- XML格式（完整数据库）
- CSV格式（结构化数据）
- 包含13,000+药物条目

**许可：**
- **学术用户免费**（需要注册）
- 注册账号：https://go.drugbank.com/public_users/sign_up
- 选择 "Academic" license
- 下载 "All Drugs" 数据集

**优点：**
- 官方权威数据
- 数据完整且更新及时
- 学术使用免费
- 包含详细的药物属性、分类、代谢信息

**数据内容：**
```
- Drug Names (generic, brand, synonyms)
- Chemical Structure (SMILES, InChI, molecular formula)
- Properties (MW, LogP, solubility, pKa, etc.)
- Classification (ATC codes, categories)
- Pharmacology (indications, mechanism of action)
- ADME data (absorption, metabolism, etc.)
- Formulations (approved products, dosage forms)
```

### 方案2：PubChem替代方案
**来源：** https://pubchem.ncbi.nlm.nih.gov/

**API访问：** PUG REST API（完全开源免费）
```
https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/MolecularWeight,XLogP,HBondDonorCount/JSON
```

**优点：**
- 完全开源免费，无需注册
- RESTful API易于集成
- 包含基础物化性质

**缺点：**
- 缺少药学分类（BCS、剂型等）
- 需要额外整合其他数据源

### 方案3：开源Python包
**推荐工具：**

1. **bioservices** - 访问多个生物医学数据库
```bash
pip install bioservices
```

```python
from bioservices import ChEBI, UniProt
# 可访问ChEBI化学本体、UniProt蛋白数据
```

2. **chembl_webresource_client** - ChEMBL数据库
```bash
pip install chembl_webresource_client
```

```python
from chembl_webresource_client.new_client import new_client
molecule = new_client.molecule
res = molecule.filter(pref_name__iexact='ibuprofen')
```

3. **rdkit** - 化学信息学工具
```bash
pip install rdkit
```

## 推荐实现方案

### Phase 1：DrugBank官方数据导入（最全面）

**步骤：**

1. **注册并下载DrugBank数据**
   - 注册学术账号
   - 下载 `drugbank_all_full_database.xml.zip`
   - 解压得到 XML 文件

2. **解析XML并提取关键数据**
   ```python
   import xml.etree.ElementTree as ET
   import pandas as pd
   
   def parse_drugbank_xml(xml_file):
       tree = ET.parse(xml_file)
       root = tree.getroot()
       
       drugs = []
       for drug in root.findall('.//{http://www.drugbank.ca}drug'):
           drug_data = {
               'drugbank_id': drug.findtext('.//{http://www.drugbank.ca}drugbank-id[@primary="true"]'),
               'name': drug.findtext('.//{http://www.drugbank.ca}name'),
               'description': drug.findtext('.//{http://www.drugbank.ca}description'),
               'cas_number': drug.findtext('.//{http://www.drugbank.ca}cas-number'),
               # Chemical properties
               'smiles': drug.findtext('.//{http://www.drugbank.ca}property[{http://www.drugbank.ca}kind="SMILES"]/{http://www.drugbank.ca}value'),
               'molecular_weight': drug.findtext('.//{http://www.drugbank.ca}property[{http://www.drugbank.ca}kind="Molecular Weight"]/{http://www.drugbank.ca}value'),
               'logp': drug.findtext('.//{http://www.drugbank.ca}property[{http://www.drugbank.ca}kind="logP"]/{http://www.drugbank.ca}value'),
               'logs': drug.findtext('.//{http://www.drugbank.ca}property[{http://www.drugbank.ca}kind="Water Solubility"]/{http://www.drugbank.ca}value'),
               # Pharmaceutical info
               'indication': drug.findtext('.//{http://www.drugbank.ca}indication'),
               'pharmacodynamics': drug.findtext('.//{http://www.drugbank.ca}pharmacodynamics'),
               'absorption': drug.findtext('.//{http://www.drugbank.ca}absorption'),
           }
           drugs.append(drug_data)
       
       return pd.DataFrame(drugs)
   ```

3. **存储到SQLite数据库**
   ```python
   import sqlite3
   
   conn = sqlite3.connect('formulation_knowledge.db')
   
   # 创建药物表
   conn.execute('''
   CREATE TABLE IF NOT EXISTS drugbank_drugs (
       drugbank_id TEXT PRIMARY KEY,
       name TEXT NOT NULL,
       description TEXT,
       cas_number TEXT,
       smiles TEXT,
       molecular_weight REAL,
       logp REAL,
       logs REAL,
       hbd INTEGER,
       hba INTEGER,
       psa REAL,
       bcs_class TEXT,
       indication TEXT,
       pharmacodynamics TEXT,
       absorption TEXT,
       metabolism TEXT,
       route_of_administration TEXT,
       approved_formulations TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   ''')
   
   df.to_sql('drugbank_drugs', conn, if_exists='replace', index=False)
   ```

4. **UI集成 - 添加搜索和浏览功能**
   ```python
   # 在 Knowledge Base -> Drug Database tab
   
   st.markdown("### 🔍 Drug Search")
   
   search_query = st.text_input("Search by drug name, CAS number, or DrugBank ID")
   
   if search_query:
       cursor = conn.execute("""
           SELECT drugbank_id, name, molecular_weight, logp, logs, bcs_class, indication
           FROM drugbank_drugs
           WHERE name LIKE ? OR drugbank_id LIKE ? OR cas_number LIKE ?
           LIMIT 50
       """, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
       
       results = cursor.fetchall()
       
       if results:
           for drug in results:
               with st.expander(f"💊 {drug[1]} ({drug[0]})"):
                   col1, col2, col3 = st.columns(3)
                   with col1:
                       st.metric("MW", f"{drug[2]:.2f} Da")
                   with col2:
                       st.metric("LogP", f"{drug[3]:.2f}")
                   with col3:
                       st.metric("LogS", f"{drug[4]:.2f}")
                   
                   if drug[5]:
                       st.info(f"**BCS Class:** {drug[5]}")
                   
                   if drug[6]:
                       st.markdown(f"**Indication:** {drug[6][:200]}...")
   ```

### Phase 2：PubChem API补充（实时查询）

**用途：** 对于DrugBank没有的化合物，实时从PubChem查询

```python
import requests

def get_pubchem_properties(drug_name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,TPSA/JSON"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['PropertyTable']['Properties'][0]
    except:
        return None
```

### Phase 3：BCS分类预测（基于规则）

```python
def predict_bcs_class(mw, logp, logs, dose_mg=None):
    """
    基于FDA BCS指南预测BCS分类
    """
    # Solubility classification (dose/250mL at pH 1-7.5)
    if dose_mg and logs:
        dose_solubility = dose_mg / 250  # mg/mL
        solubility_mgml = 10**(logs) * mw  # mol/L to mg/mL
        high_solubility = solubility_mgml >= dose_solubility
    else:
        # 简化规则：LogS > -4 为高溶解度
        high_solubility = logs > -4
    
    # Permeability classification (approximation from LogP)
    # LogP 0-3 通常有较好的渗透性
    high_permeability = 0 < logp < 3
    
    if high_solubility and high_permeability:
        return "BCS I"
    elif not high_solubility and high_permeability:
        return "BCS II"
    elif high_solubility and not high_permeability:
        return "BCS III"
    else:
        return "BCS IV"
```

## 实施时间表

**Week 1：数据获取与解析**
- [ ] 注册DrugBank学术账号
- [ ] 下载完整数据集（XML格式）
- [ ] 编写XML解析脚本
- [ ] 验证数据完整性

**Week 2：数据库设计与导入**
- [ ] 设计药物数据库schema
- [ ] 数据清洗和标准化
- [ ] 导入到SQLite
- [ ] 添加BCS分类预测

**Week 3：UI集成**
- [ ] 药物搜索功能
- [ ] 药物详情页面
- [ ] 按BCS分类浏览
- [ ] 按适应症分类浏览

**Week 4：测试与优化**
- [ ] 数据质量验证
- [ ] 性能优化（索引、缓存）
- [ ] 用户体验测试

## 法律与伦理考虑

1. **DrugBank License：**
   - 学术使用免费
   - 禁止商业用途
   - 需注明数据来源
   - 定期更新（每6-12月）

2. **引用格式：**
   ```
   Wishart DS, et al. DrugBank 6.0: the DrugBank knowledgebase for 2024. 
   Nucleic Acids Res. 2024 Jan 5;52(D1):D1265-D1275.
   ```

3. **隐私保护：**
   - 仅使用公开药物数据
   - 不存储患者个人信息

## 预期成果

**数据规模：**
- 13,000+ FDA批准和实验性药物
- 覆盖90%常用制剂药物
- 包含详细物化性质和药学分类

**功能增强：**
- 实时药物查询
- BCS分类自动预测
- 制剂策略推荐依据增强
- 支持批量药物分析

**展示价值：**
- 体现系统的数据完整性
- 增强学术可信度
- 支持真实案例研究

## 下一步行动

1. **立即执行：** 注册DrugBank学术账号并申请数据访问
2. **并行开发：** 实现PubChem API集成作为backup
3. **UI原型：** 先在本地实现药物搜索功能测试
4. **数据验证：** 选择10个代表性药物验证数据准确性

---

需要我开始实现吗？我可以先帮你：
1. 注册DrugBank账号的指导
2. 编写DrugBank XML解析脚本
3. 实现PubChem API集成
4. 设计药物搜索UI界面
