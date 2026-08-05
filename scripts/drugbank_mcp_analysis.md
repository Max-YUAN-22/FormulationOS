# DrugBank MCP Integration for FormulationOS

## 新发现：DrugBank MCP服务

### 什么是MCP？
Model Context Protocol - 允许AI工具直接连接到DrugBank的知识库，实时查询药物数据。

### MCP服务信息
- **MCP URL**: https://mcp.drugbank.com/mcp
- **支持工具**: ChatGPT, Claude, Gemini, CLI, Copilot等
- **认证**: 需要DrugBank OS付费账号 + MCP访问权限
- **联系**: 需要contact sales启用

## 方案对比

### 方案1: DrugBank MCP（新方案）✨

**优势：**
- ✅ **实时数据** - 无需下载维护本地数据库
- ✅ **AI原生** - Claude/GPT可直接理解DrugBank数据
- ✅ **专家策划** - 避免AI幻觉，数据可追溯
- ✅ **深度关联** - 药物-靶点-疾病-通路完整关系网
- ✅ **竞争情报** - 管线活动、临床进展跟踪

**劣势：**
- ❌ **需要付费** - DrugBank OS账号 + MCP访问（价格未知）
- ❌ **需联系销售** - 可能需要商业或机构许可
- ⚠️ **未知限制** - API调用限制、定价模式待确认

**适用场景：**
- 有预算的商业项目
- 需要最新、最全面的药物数据
- 需要AI直接回答复杂药物问题

### 方案2: 免费DrugBank下载 + 本地数据库（原方案）

**优势：**
- ✅ **学术免费** - 注册即可下载
- ✅ **完全控制** - 数据在本地，无API限制
- ✅ **离线可用** - 不依赖网络
- ✅ **可定制** - 按需索引、搜索、展示

**劣势：**
- ❌ **需手动更新** - 6-12个月更新一次
- ❌ **开发工作量** - 需要解析XML、建数据库
- ❌ **存储占用** - 本地需要存储完整数据

**适用场景：**
- 学术研究项目
- 预算有限
- 需要完全控制数据

### 方案3: PubChem API（备选免费方案）

**优势：**
- ✅ **完全免费** - 无需注册
- ✅ **RESTful API** - 易于集成
- ✅ **实时查询** - 无需维护本地数据

**劣势：**
- ❌ **数据有限** - 缺少BCS分类、剂型等药学信息
- ❌ **需额外整合** - 药学数据需从其他源补充

**适用场景：**
- 快速原型验证
- 基础化合物查询
- 作为其他方案的补充

## FormulationOS集成方案

### 推荐策略：混合方案

```
┌─────────────────────────────────────────┐
│      FormulationOS Knowledge Base       │
└─────────────────────────────────────────┘
              ↓ 查询药物信息
      ┌───────┴────────┐
      ↓                ↓
┌──────────┐    ┌──────────────┐
│ PubChem  │    │ Local Cache  │
│   API    │    │  (SQLite)    │
│ (免费)    │    │              │
└──────────┘    └──────────────┘
   基础性质         缓存 + BCS分类预测

未来扩展：
┌──────────────────────────────────────┐
│  DrugBank MCP (如果获得访问权限)       │
│  - 完整药物知识                         │
│  - AI深度问答                          │
│  - 竞争情报                            │
└──────────────────────────────────────┘
```

### 实施步骤

#### Phase 1: 立即实现 - PubChem集成（今天完成）

```python
# src/formulation_os/knowledge/drug_database.py

import requests
import streamlit as st
from typing import Optional, Dict

class DrugDatabase:
    """药物数据库查询接口"""
    
    def __init__(self):
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.cache_db = "formulation_knowledge.db"
    
    def search_drug(self, drug_name: str) -> Optional[Dict]:
        """
        搜索药物信息
        优先级: Local Cache > PubChem API > DrugBank MCP (if available)
        """
        # 1. 先查本地缓存
        cached = self._get_from_cache(drug_name)
        if cached:
            return cached
        
        # 2. 查询PubChem
        pubchem_data = self._query_pubchem(drug_name)
        if pubchem_data:
            # 预测BCS分类
            pubchem_data['bcs_class'] = self._predict_bcs_class(pubchem_data)
            # 缓存结果
            self._save_to_cache(drug_name, pubchem_data)
            return pubchem_data
        
        # 3. TODO: 如果有DrugBank MCP权限，查询DrugBank
        # drugbank_data = self._query_drugbank_mcp(drug_name)
        
        return None
    
    def _query_pubchem(self, drug_name: str) -> Optional[Dict]:
        """从PubChem查询药物基础性质"""
        properties = [
            'MolecularWeight',
            'XLogP',
            'HBondDonorCount',
            'HBondAcceptorCount',
            'TPSA',
            'IUPACName',
            'CanonicalSMILES'
        ]
        
        url = f"{self.pubchem_base}/compound/name/{drug_name}/property/{','.join(properties)}/JSON"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()['PropertyTable']['Properties'][0]
                
                return {
                    'source': 'PubChem',
                    'name': drug_name,
                    'cid': data.get('CID'),
                    'molecular_weight': data.get('MolecularWeight'),
                    'logp': data.get('XLogP'),
                    'hbd': data.get('HBondDonorCount'),
                    'hba': data.get('HBondAcceptorCount'),
                    'tpsa': data.get('TPSA'),
                    'smiles': data.get('CanonicalSMILES'),
                    'iupac_name': data.get('IUPACName')
                }
        except Exception as e:
            print(f"PubChem query failed: {e}")
            return None
    
    def _predict_bcs_class(self, drug_data: Dict) -> str:
        """基于物化性质预测BCS分类"""
        mw = drug_data.get('molecular_weight', 0)
        logp = drug_data.get('logp', 0)
        hbd = drug_data.get('hbd', 0)
        hba = drug_data.get('hba', 0)
        tpsa = drug_data.get('tpsa', 0)
        
        # 简化的BCS预测规则
        # 高溶解度: MW<500, LogP<5, TPSA适中
        high_solubility = (mw < 500 and logp < 5)
        
        # 高渗透性: LogP 0-3, TPSA<140, HBD<5
        high_permeability = (0 < logp < 3 and tpsa < 140 and hbd < 5)
        
        if high_solubility and high_permeability:
            return "BCS I"
        elif not high_solubility and high_permeability:
            return "BCS II"
        elif high_solubility and not high_permeability:
            return "BCS III"
        else:
            return "BCS IV"
    
    def _get_from_cache(self, drug_name: str) -> Optional[Dict]:
        """从本地缓存获取"""
        # TODO: 实现SQLite缓存查询
        pass
    
    def _save_to_cache(self, drug_name: str, data: Dict):
        """保存到本地缓存"""
        # TODO: 实现SQLite缓存存储
        pass
```

#### Phase 2: UI集成到Knowledge Base

```python
# 在 FormulationOS_Enterprise.py的Knowledge Base -> Drug Database tab

with tab1:  # Drug Database
    st.markdown("### 🔍 Drug Information Search")
    st.caption("Powered by PubChem + BCS Prediction Algorithm")
    
    drug_query = st.text_input("Enter drug name (e.g., Ibuprofen, Metoprolol)")
    
    if drug_query:
        with st.spinner(f"Searching {drug_query}..."):
            db = DrugDatabase()
            result = db.search_drug(drug_query)
            
            if result:
                st.success(f"✅ Found: **{result['name']}**")
                
                # 性质卡片
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Molecular Weight", f"{result['molecular_weight']:.2f} Da")
                with col2:
                    st.metric("LogP", f"{result['logp']:.2f}")
                with col3:
                    st.metric("HBD / HBA", f"{result['hbd']} / {result['hba']}")
                with col4:
                    st.metric("TPSA", f"{result['tpsa']:.1f} Ų")
                
                # BCS分类
                st.markdown("---")
                bcs_class = result.get('bcs_class', 'Unknown')
                bcs_colors = {
                    'BCS I': '🟢',
                    'BCS II': '🟡',
                    'BCS III': '🟠',
                    'BCS IV': '🔴'
                }
                st.info(f"{bcs_colors.get(bcs_class, '⚪')} **Predicted BCS Classification:** {bcs_class}")
                
                # SMILES
                if result.get('smiles'):
                    with st.expander("🧬 Chemical Structure"):
                        st.code(result['smiles'], language='text')
                        # TODO: 如果有rdkit，显示分子结构图
                
                # 制剂策略推荐
                with st.expander("💊 Recommended Formulation Strategies"):
                    if bcs_class == 'BCS I':
                        st.markdown("""
                        - ✅ Immediate-release tablets/capsules
                        - ✅ Standard formulation approaches
                        - ℹ️ Focus on stability and manufacturing
                        """)
                    elif bcs_class == 'BCS II':
                        st.markdown("""
                        - 🎯 Amorphous Solid Dispersion (ASD)
                        - 🎯 Nanocrystal technology
                        - 🎯 Lipid-based formulations (SEDDS)
                        - ⚠️ Avoid cyclodextrin if dose >200mg
                        """)
                    # ... 其他BCS分类的策略
                
                st.caption(f"📊 Data source: {result['source']}")
            else:
                st.error(f"❌ Drug '{drug_query}' not found in PubChem")
    
    # 显示已有的BCS分类知识库（保留原内容）
    st.markdown("---")
    st.markdown("### 📚 BCS Classification Knowledge Base")
    # ... 原有的BCS分类expander内容
```

#### Phase 3: DrugBank MCP集成（如果获得访问权限）

**需要的信息：**
1. 联系DrugBank sales确认：
   - 学术研究是否有折扣
   - MCP访问的定价模式
   - API调用限制
   - 是否支持programmatic access（不只是ChatGPT界面）

2. 如果获得访问：
```python
# 可能的集成方式（取决于MCP的实际API）

from anthropic import Anthropic

def query_drugbank_mcp(drug_name: str, question: str) -> str:
    """
    通过Claude + DrugBank MCP查询药物信息
    """
    client = Anthropic(api_key=CLAUDE_API_KEY)
    
    # 如果DrugBank MCP已配置，Claude可以直接访问DrugBank数据
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Using DrugBank data, tell me about {drug_name}: {question}"
        }]
    )
    
    return response.content[0].text
```

## 成本估算

### PubChem（免费）
- ✅ 完全免费
- ✅ 无API限制（合理使用）

### DrugBank下载（学术免费）
- ✅ 免费下载
- ✅ 一次性开发成本

### DrugBank MCP（价格待确认）
- ❓ 可能按月订阅
- ❓ 可能按API调用计费
- ❓ 学术折扣？

## 下一步行动

### 立即执行（今天）：
1. ✅ 实现PubChem API集成
2. ✅ 添加药物搜索UI到Knowledge Base
3. ✅ 实现BCS分类预测算法
4. ✅ 本地测试验证

### 并行调研（本周）：
1. 📧 联系DrugBank sales询问MCP访问：
   - 发邮件到：sales@drugbank.com
   - 说明是学术研究项目
   - 询问定价和学术折扣
2. 🔍 测试MCP在Claude Desktop的使用体验
3. 📝 评估成本效益

### 长期规划（如果预算允许）：
1. 升级到DrugBank MCP
2. 替换PubChem为DrugBank作为主数据源
3. 保留PubChem作为备份

## 演示策略

**向教授展示时：**
1. **现阶段**：展示PubChem集成
   - "我们集成了PubChem API，可以实时查询任何化合物的性质"
   - "基于Lipinski规则和BCS指南预测分类"

2. **未来规划**：提及DrugBank MCP
   - "我们正在评估DrugBank的MCP服务"
   - "这将提供更全面的药物知识和竞争情报"

3. **技术优势**：
   - "系统采用渐进式数据源策略"
   - "可以根据需求和预算灵活切换数据源"

---

**需要我现在开始实现PubChem集成吗？**
这样你就能立即在Knowledge Base中搜索任何药物了！
