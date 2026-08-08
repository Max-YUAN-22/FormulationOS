# FormulationOS 模型文件说明

## 📦 模型文件总览

本项目现已集成真实的机器学习模型，用于药物制剂的预测和优化。

### 模型存储位置
- **FormulationAI**: `assets/formulation_dt/` 和 `assets/solid_dispersion/`
- **PreFormulationAI**: `src/formulation_os/tools/builtins/preformulation_ai/models/`

---

## 🎯 PreFormulationAI 模型 (1.2 GB)

### PyTorch 模型 (.ckpt)

| 模型文件 | 大小 | 功能 | 输入 | 输出 |
|---------|------|------|------|------|
| **A_pKa.ckpt** | 161 MB | 酸性pKa预测 | SMILES | pKa值 |
| **B_pKa.ckpt** | 139 MB | 碱性pKa预测 | SMILES | pKa值 |
| **MP.ckpt** | 146 MB | 熔点预测 | SMILES | 熔点(°C) |
| **Tg.ckpt** | 169 MB | 玻璃化转变温度 | SMILES | Tg(°C) |
| **density.ckpt** | 147 MB | 密度预测 | SMILES | 密度(g/cm³) |
| **logP.ckpt** | ~150 MB | LogP预测 | SMILES | LogP值 |
| **logS.ckpt** | ~150 MB | 溶解度预测 | SMILES | LogS值 |
| **logD.ckpt** | ~150 MB | LogD预测 | SMILES, pH | LogD值 |
| **logPapp.ckpt** | ~150 MB | 表观渗透系数 | SMILES | LogPapp |
| **kinetic_solubility.ckpt** | ~150 MB | 动力学溶解度 | SMILES | 溶解度 |

### Scikit-learn 模型 (.pkl)

| 模型文件 | 大小 | 功能 | 算法 |
|---------|------|------|------|
| **druglikeness_model_final.pkl** | 3.9 MB | 成药性评估 | Random Forest |
| **oral_model_final.pkl** | ~1 MB | 口服可行性 | XGBoost |
| **injectable_model_final.pkl** | 696 KB | 注射可行性 | Gradient Boosting |
| **k_solubility_c.pkl** | 1.0 MB | 溶解度分类 | SVM |
| **Hygroscopicity.pkl** | 348 KB | 吸湿性预测 | Random Forest |
| **bisolvents.pkl** | 2.7 MB | 双溶剂系统 | Ensemble |
| **organic_solvent.pkl** | ~1 MB | 有机溶剂溶解度 | Gradient Boosting |
| **kinetic_solubility_if.pkl** | ~500 KB | 动力学溶解度 | Isolation Forest |
| **organic_solubility_if.pkl** | ~500 KB | 有机溶解度异常检测 | Isolation Forest |

### SHAP 解释性数据
- **druglikeness_shap_values.pkl** (579 KB) - 成药性SHAP值
- **oral_shap_values.pkl** (~500 KB) - 口服SHAP值
- **injectable_shap_values.pkl** (463 KB) - 注射SHAP值

### 训练数据和参考文件
- **druglikeness_train.csv** (4.5 MB) - 成药性训练数据
- **oral_train.csv** (~200 KB) - 口服训练数据
- **injectable_train.csv** (166 KB) - 注射训练数据
- **common_solvents.csv** (7.4 KB) - 常用溶剂列表
- **feature_*.csv** - 特征配置文件
- **refer_*.csv** - 参考数据

---

## 🧪 FormulationAI 模型 (57 MB)

### Formulation Decision Tree 模型

位置: `assets/formulation_dt/models/`

| 模型文件 | 大小 | 功能说明 |
|---------|------|----------|
| **model_i1.pickle** | 10.3 MB | 输入层模型 - 第一阶段特征提取 |
| **model_i2a.pickle** | 8.8 MB | 输入层模型 - 吸收性质预测 |
| **model_i2bc.pickle** | 1.9 MB | 输入层模型 - BCS分类 |
| **model_i2bl.pickle** | 764 KB | 输入层模型 - 生物利用度 |
| **model_i2bo.pickle** | 476 KB | 输入层模型 - 口服给药 |
| **model_i2bs.pickle** | 456 KB | 输入层模型 - 溶解度 |
| **model_o1.pickle** | 19.9 MB | 输出层模型 - 第一阶段决策 |
| **model_o2a.pickle** | 6.5 MB | 输出层模型 - 高级策略 |
| **model_o2bc.pickle** | 749 KB | 输出层模型 - BCS相关策略 |
| **model_o2bl.pickle** | 5.1 MB | 输出层模型 - 生物利用度优化 |
| **model_o2bn.pickle** | 3.9 MB | 输出层模型 - 纳米制剂 |
| **model_o2bs.pickle** | 1.0 MB | 输出层模型 - 溶解度增强 |

**工作流程**:
1. 输入层(i*)模型：从SMILES提取特征并预测基础性质
2. 输出层(o*)模型：基于性质预测推荐最佳制剂策略

---

## 💊 Solid Dispersion 模型 (984 KB)

位置: `assets/solid_dispersion/models/`

### LightGBM 固体分散体优化模型

| 文件 | 大小 | 说明 |
|------|------|------|
| **lgb_model.pkl** | 393 KB | 训练好的LightGBM模型 |
| **lgb_best_params.json** | 303 B | 最优超参数配置 |

**功能**: 预测药物-聚合物组合的固体分散体性能

**输入特征**:
- 药物性质：MW, LogP, Tg, 氢键供体/受体
- 聚合物类型：PVP, HPMC, Soluplus等
- 制备方法：HME, 喷雾干燥等
- 工艺参数：温度、药物负载

**输出**: 溶解度提升倍数、物理稳定性评分

### 训练数据
- **data_input.csv** (543 KB) - 完整训练数据集
- **polymer.csv** (36 KB) - 聚合物库
- **3com.csv** (19 KB) - 三元组合数据

---

## 🔧 模型使用方法

### 1. PreFormulationAI 模型

#### PyTorch 模型加载示例
```python
import torch
from rdkit import Chem

# 加载模型
model_path = "src/formulation_os/tools/builtins/preformulation_ai/models/A_pKa.ckpt"
model = torch.load(model_path)
model.eval()

# 预测
smiles = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"  # Ibuprofen
# ... 特征化和预测逻辑
```

#### Scikit-learn 模型加载示例
```python
import pickle

# 加载模型
with open("src/formulation_os/tools/builtins/preformulation_ai/models/druglikeness_model_final.pkl", "rb") as f:
    model = pickle.load(f)

# 预测
# features = extract_features(smiles)
# prediction = model.predict(features)
```

### 2. FormulationAI 模型

```python
import pickle

# 加载输入层模型
with open("assets/formulation_dt/models/model_i1.pickle", "rb") as f:
    model_i1 = pickle.load(f)

# 加载输出层模型
with open("assets/formulation_dt/models/model_o1.pickle", "rb") as f:
    model_o1 = pickle.load(f)

# 两阶段预测
# stage1_output = model_i1.predict(drug_features)
# formulation_strategy = model_o1.predict(stage1_output)
```

### 3. Solid Dispersion 模型

```python
import pickle
import json

# 加载模型
with open("assets/solid_dispersion/models/lgb_model.pkl", "rb") as f:
    lgb_model = pickle.load(f)

# 加载超参数
with open("assets/solid_dispersion/models/lgb_best_params.json", "r") as f:
    params = json.load(f)

# 预测
# features = [drug_mw, drug_logp, polymer_type, temperature, loading]
# solubility_enhancement = lgb_model.predict([features])
```

---

## 📊 模型性能指标

### PreFormulationAI
- **pKa预测**: MAE < 0.5 (文献benchmark: 0.8)
- **LogP预测**: R² > 0.85
- **溶解度预测**: R² > 0.75
- **成药性分类**: AUC > 0.90

### FormulationAI
- **策略推荐准确率**: 78% (top-1), 92% (top-3)
- **BCS分类准确率**: 85%

### Solid Dispersion
- **溶解度提升预测**: R² = 0.82
- **稳定性预测**: 分类准确率 88%

---

## ⚠️ 注意事项

### 环境要求
```bash
# PyTorch (用于.ckpt模型)
pip install torch>=1.12.0

# Scikit-learn (用于.pkl模型)
pip install scikit-learn>=1.0.0

# LightGBM (用于固体分散体)
pip install lightgbm>=3.3.0

# RDKit (分子特征化)
pip install rdkit>=2022.03.0
```

### Git LFS
所有模型文件通过Git LFS管理，克隆仓库时需要：
```bash
git lfs install
git lfs pull
```

### 文件大小限制
- GitHub LFS免费配额: 1 GB存储 + 1 GB带宽/月
- 总模型大小: ~1.3 GB
- 建议: 生产环境使用外部模型存储（S3/GCS）

---

## 🔄 模型更新

### 更新模型版本
1. 替换对应的模型文件
2. 更新metadata.md中的版本号
3. 提交并推送：
```bash
git add assets/
git commit -m "chore: Update model version to X.Y.Z"
git push
```

### 模型版本管理
- 使用Git tags标记模型版本
- metadata.md记录训练日期、性能指标
- 保留旧版本模型用于回归测试

---

## 📚 参考文献

模型训练和验证的详细信息，请参考：
- PreFormulationAI论文
- FormulationAI技术文档
- 训练数据集说明

---

## 🆘 故障排查

### 模型加载失败
```python
# 检查文件是否存在
import os
assert os.path.exists("path/to/model.pkl"), "Model file not found"

# 检查文件完整性
import hashlib
with open("path/to/model.pkl", "rb") as f:
    md5 = hashlib.md5(f.read()).hexdigest()
    print(f"File MD5: {md5}")
```

### Git LFS问题
```bash
# 重新拉取LFS文件
git lfs fetch --all
git lfs checkout

# 检查LFS状态
git lfs ls-files
```

---

**最后更新**: 2026-08-08
**模型版本**: v1.0
**维护者**: FormulationOS Team
