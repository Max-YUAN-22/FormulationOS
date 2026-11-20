# Pilot 30题 审计文档(供与教授讨论用)

## Q1 [A_numeric] ABACAVIR
**问**: ABACAVIR 的分子量是多少？只回答数值（单位 g/mol）。
**裸LLM答**: 286.33
→ 判分: ✓  
**查库答**: 286.33
→ 判分: ✓  (调用DB: True)

## Q2 [A_numeric] ABACAVIR
**问**: ABACAVIR 的XLogP是多少？只回答数值。
**裸LLM答**: 1.2
→ 判分: ✗ 错误  
**查库答**: 0.9
→ 判分: ✓  (调用DB: True)

## Q3 [A_numeric] ABACAVIR
**问**: ABACAVIR 的实验熔点是多少？只回答数值。
**裸LLM答**: 165–166
→ 判分: ✓  
**查库答**: 165 °C
→ 判分: ✓  (调用DB: True)

## Q4 [A_numeric] ABACAVIR
**问**: ABACAVIR 的半衰期是多少？只回答数值（单位 h）。
**裸LLM答**: 1.5
→ 判分: ✗ 错误  
**查库答**: 1.54 h
→ 判分: ✗ 错误  (调用DB: True)

## Q5 [A_numeric] ABACAVIR
**问**: ABACAVIR 的最强酸性pKa是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 15.41
→ 判分: ✓  (调用DB: True)

## Q6 [A_numeric] ABACAVIR SULFATE
**问**: ABACAVIR SULFATE 的分子量是多少？只回答数值（单位 g/mol）。
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 670.7
→ 判分: ✓  (调用DB: True)

## Q7 [A_numeric] Abemaciclib
**问**: Abemaciclib 的分子量是多少？只回答数值（单位 g/mol）。
**裸LLM答**: 506.60
→ 判分: ✓  
**查库答**: 506.6
→ 判分: ✓  (调用DB: True)

## Q8 [A_numeric] Abemaciclib
**问**: Abemaciclib 的XLogP是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 3.8
→ 判分: ✓  (调用DB: True)

## Q9 [A_numeric] Abemaciclib
**问**: Abemaciclib 的半衰期是多少？只回答数值（单位 h）。
**裸LLM答**: 18.3
→ 判分: ✓  
**查库答**: 18.3
→ 判分: ✓  (调用DB: True)

## Q10 [A_numeric] Abemaciclib
**问**: Abemaciclib 的最强酸性pKa是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 10.27
→ 判分: ✓  (调用DB: True)

## Q11 [A_numeric] Abiraterone
**问**: Abiraterone 的分子量是多少？只回答数值（单位 g/mol）。
**裸LLM答**: 349.51
→ 判分: ✓  
**查库答**: 349.5
→ 判分: ✓  (调用DB: True)

## Q12 [A_numeric] Abiraterone
**问**: Abiraterone 的XLogP是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 4.6
→ 判分: ✓  (调用DB: True)

## Q13 [B_entity] Acyclovir
**问**: Acyclovir 的分子量是多少？只回答数值。
**裸LLM答**: 225.21
→ 判分: ✓  (verdict=parent)
**查库答**: 225.2
→ 判分: ✓  (调用DB: True)

## Q14 [B_entity] Adefovir
**问**: Adefovir 的分子量是多少？只回答数值。
**裸LLM答**: 273.19
→ 判分: ✓  (verdict=parent)
**查库答**: 273.19
→ 判分: ✓  (调用DB: True)

## Q15 [B_entity] Alogliptin
**问**: Alogliptin 的分子量是多少？只回答数值。
**裸LLM答**: 339.39
→ 判分: ✓  (verdict=parent)
**查库答**: 339.4
→ 判分: ✓  (调用DB: True)

## Q16 [B_entity] AMPHETAMINE ASPARTATE
**问**: AMPHETAMINE ASPARTATE 的分子量是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  (verdict=wrong)
**查库答**: 403.5
→ 判分: ✗ 错误  (调用DB: True)

## Q17 [B_entity] AMPHETAMINE SULFATE
**问**: AMPHETAMINE SULFATE 的分子量是多少？只回答数值。
**裸LLM答**: 368.49
→ 判分: ✗ 错误  (verdict=salt)
**查库答**: 368.5
→ 判分: ✗ 错误  (调用DB: True)

## Q18 [B_entity] ANISOTROPINE
**问**: ANISOTROPINE 的分子量是多少？只回答数值。
**裸LLM答**: 
→ 判分: ✗ 错误  (verdict=wrong)
**查库答**: 267.41
→ 判分: ✓  (调用DB: True)

## Q19 [C_evidence] ABACAVIR
**问**: ABACAVIR 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: 
→ 判分: ✓  (调用DB: True)

## Q20 [C_evidence] Abemaciclib
**问**: Abemaciclib 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: 
→ 判分: ✓  (调用DB: False)

## Q21 [C_evidence] Abiraterone
**问**: Abiraterone 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: API Error: Expecting value: line 1 column 1 (char 0)
→ 判分: ✓  (调用DB: True)

## Q22 [C_evidence] ABROCITINIB
**问**: ABROCITINIB 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: 
→ 判分: ✓  (调用DB: True)

## Q23 [C_evidence] ACALABRUTINIB
**问**: ACALABRUTINIB 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: 
→ 判分: ✓  (调用DB: True)

## Q24 [C_evidence] ACAMPROSATE
**问**: ACAMPROSATE 的 pKa 是多少？这个数值是实验测定的还是计算预测的？
**裸LLM答**: 
→ 判分: ✓  
**查库答**: 
→ 判分: ✓  (调用DB: True)

## Q25 [D_strategy] ABACAVIR
**问**: 针对 ABACAVIR，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: 针对 Abacavir（阿巴卡韦，常用硫酸盐）的制剂策略建议：

1. **口服速释片剂**：300 mg（按阿巴卡韦计）薄膜包衣片，为最常用剂型。  
2. **口服溶液剂**：如 20 mg/mL，适用于儿童或吞咽困难患者，需注意掩味。  
3. **复方单片制剂**：与拉米夫定、多替拉韦等组成固定剂量
→ 判分: ✗ 错误  
**查库答**: ## ABACAVIR 制剂策略分析

### 1. BCS 分类及依据

**结论：BCS III 类（高溶解、中/低渗透）为主流共识；计算模型给出 BCS II 类，需以实测盐型数据校正。**

| 数据来源 | 数值 | 意义 |
|---|---|---|
| 计算 logS（游离碱） | -3.0（约 0.1 mg/mL） | 游离碱溶解度较低 → 计算模型判 BCS II |
| FDA 标签实测（硫酸盐） | **77 m
→ 判分: ✓  (调用DB: True)

## Q26 [D_strategy] ABACAVIR SULFATE
**问**: 针对 ABACAVIR SULFATE，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: 针对硫酸阿巴卡韦（abacavir sulfate），建议采用以下剂型：

1. **速释薄膜包衣片**：最常用，规格以阿巴卡韦计 300 mg/片，便于口服、掩味及避光防潮。
2. **口服溶液**：规格 20 mg/mL，适用于儿童或吞咽困难患者。
3. **分散片/口崩片**：可作为儿科或特殊人群的改良剂型，提高顺应性。
4. **固定剂量复方片**：与拉米夫定、多替拉韦等组成单片复方制剂，提高依从性。

不推荐制成缓释/
→ 判分: ✗ 错误  
**查库答**: 
→ 判分: ✗ 错误  (调用DB: True)

## Q27 [D_strategy] Abiraterone
**问**: 针对 Abiraterone，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: 针对 Abiraterone（醋酸阿比特龙）可采用以下制剂策略：

1. **纳米晶体片/胶囊**：减小粒径，提高溶出速率和口服生物利用度，降低食物效应。  
2. **无定形固体分散体片**：通过载体抑制结晶，提高表观溶解度和溶出度。  
3. **自微乳化/自乳化递药系统（SMEDDS/SNEDDS）**：利用脂质增溶，改善吸收并减少食物
→ 判分: ✗ 错误  
**查库答**: ## Abiraterone 制剂策略分析

### 1. BCS 分类与依据
**结论：BCS II 类（低溶解性、高渗透性）**
- 溶解性：LogS = −3.0 ~ −5.1（多源数据），动力学溶解度约 0.1 mg/mL（AI 预测）或 ~1 mg/L（水，25°C）——**溶解度极低，属"难溶"**。
- 渗透性：LogP = 2.5（AI）~ 5.1（DrugBank），TPSA = 33 Å²，HBD=1、HBA=2，M
→ 判分: ✗ 错误  (调用DB: True)

## Q28 [D_strategy] ABIRATERONE ACETATE
**问**: 针对 ABIRATERONE ACETATE，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: 
→ 判分: ✗ 错误  
**查库答**: 
→ 判分: ✗ 错误  (调用DB: True)

## Q29 [D_strategy] ABROCITINIB
**问**: 针对 ABROCITINIB，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: Abrocitinib 推荐采用**口服薄膜包衣片**剂型，便于每日一次给药和剂量调整（常用规格：50 mg、100 mg、150 mg、200 mg）。
→ 判分: ✗ 错误  
**查库答**: API Error: Unterminated string starting at: line 1 column 40 (char 39)
→ 判分: ✗ 错误  (调用DB: False)

## Q30 [D_strategy] ACALABRUTINIB
**问**: 针对 ACALABRUTINIB，应采用什么制剂策略（给出剂型建议即可）？
**裸LLM答**: 针对 acalabrutinib，建议采用**口服速释硬胶囊剂**。

具体策略要点：
- 使用 **acalabrutinib 马来酸盐** 形式，改善溶解性与化学稳定性。
- 可采用 **微粉化或纳米化** 处理原料药，提高溶出速率。
- 处方中配伍适宜填充剂、崩解剂和润滑剂，制成内容物为粉末或颗粒的硬胶囊。
- 剂型以 **速释** 为主，便于口服
→ 判分: ✗ 错误  
**查库答**: 
→ 判分: ✗ 错误  (调用DB: False)


## 裸LLM错误清单(16题,需人工审计哪些是真错/判分误杀)
- Q2 [A_numeric] ABACAVIR
- Q4 [A_numeric] ABACAVIR
- Q5 [A_numeric] ABACAVIR
- Q6 [A_numeric] ABACAVIR SULFATE
- Q8 [A_numeric] Abemaciclib
- Q10 [A_numeric] Abemaciclib
- Q12 [A_numeric] Abiraterone
- Q16 [B_entity] AMPHETAMINE ASPARTATE
- Q17 [B_entity] AMPHETAMINE SULFATE
- Q18 [B_entity] ANISOTROPINE
- Q25 [D_strategy] ABACAVIR
- Q26 [D_strategy] ABACAVIR SULFATE
- Q27 [D_strategy] Abiraterone
- Q28 [D_strategy] ABIRATERONE ACETATE
- Q29 [D_strategy] ABROCITINIB
- Q30 [D_strategy] ACALABRUTINIB

## 查库后错误清单(8题)
- Q4 [A_numeric] ABACAVIR
- Q16 [B_entity] AMPHETAMINE ASPARTATE
- Q17 [B_entity] AMPHETAMINE SULFATE
- Q26 [D_strategy] ABACAVIR SULFATE
- Q27 [D_strategy] Abiraterone
- Q28 [D_strategy] ABIRATERONE ACETATE
- Q29 [D_strategy] ABROCITINIB
- Q30 [D_strategy] ACALABRUTINIB