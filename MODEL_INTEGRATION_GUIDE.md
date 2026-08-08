# FormulationOS 模型数据集成指南

## 📦 待集成的模型数据文件

### 位置
`/Users/Apple/Desktop/FormulationOS/`

### 文件清单
1. **FormulationAI Assets.zip** (5.0 MB)
   - 用途：FormulationAI 2.0 模型和数据
   - 目标位置：项目根目录

2. **PreFormulation Files.z01 + PreFormulation Files.zip** (1.1 GB)
   - 用途：PreFormulation 模型和数据
   - 目标位置：runner目录下的files文件夹
   - 注意：分卷压缩，需要两个文件都在同一目录

---

## 🔧 集成步骤（推荐手动操作）

### 步骤1: 解压 FormulationAI Assets

**方法A: 使用Finder（推荐）**
```
1. 在Finder中打开：/Users/Apple/Desktop/FormulationOS/
2. 双击 "FormulationAI Assets.zip"
3. 等待macOS自动解压
4. 将解压出的文件夹内容复制到：/Users/Apple/FormulationOS/
```

**方法B: 使用命令行**
```bash
cd /Users/Apple/FormulationOS
unzip "/Users/Apple/Desktop/FormulationOS/FormulationAI Assets.zip"
```

**预期结果**：
- 在项目根目录应该出现FormulationAI相关的模型文件
- 可能包含：models/, assets/, config/等文件夹

---

### 步骤2: 解压 PreFormulation Files（分卷压缩）

**方法A: 使用The Unarchiver（推荐）**
```
1. 安装 The Unarchiver (免费App Store应用)
2. 确保两个文件在同一目录：
   - PreFormulation Files.z01
   - PreFormulation Files.zip
3. 双击 PreFormulation Files.zip
4. The Unarchiver会自动识别分卷并解压
```

**方法B: 使用Keka（推荐）**
```
1. 安装 Keka (免费解压工具)
2. 右键点击 PreFormulation Files.zip
3. 选择 "用Keka打开"
4. 自动识别并解压所有分卷
```

**方法C: 使用命令行（需要安装p7zip）**
```bash
# 安装p7zip
brew install p7zip

# 解压分卷文件
cd /Users/Apple/Desktop/FormulationOS
7z x "PreFormulation Files.zip"
```

**预期结果**：
- 应该得到一个 `files` 文件夹
- 文件夹大小约1.1GB

---

### 步骤3: 放置 PreFormulation Files

**目标位置**：`/Users/Apple/FormulationAI/apps/runner/src/runner/ml_modules/solid_dispersion/files/`

（根据你之前的环境配置）

**操作**：
```bash
# 假设解压得到 files/ 文件夹
cd /Users/Apple/Desktop/FormulationOS
mv files/ /Users/Apple/FormulationAI/apps/runner/src/runner/ml_modules/solid_dispersion/
```

或者，如果runner在FormulationOS项目内：
```bash
cd /Users/Apple/Desktop/FormulationOS
mv files/ /Users/Apple/FormulationOS/runner/
```

---

## 📊 集成后的目录结构

### FormulationAI 集成后
```
FormulationOS/
├── assets/              # FormulationAI资源文件
│   └── formulation_dt/
├── models/              # 可能包含的模型文件
├── src/
│   └── formulation_os/
│       └── tools/
│           └── builtins/
│               └── formulation_ai/  # FormulationAI工具
└── FormulationOS_Enterprise.py
```

### PreFormulation 集成后
```
runner/
└── files/              # PreFormulation模型数据
    ├── models/
    ├── data/
    └── config/
```

---

## 🔍 验证集成

### 检查 FormulationAI
```bash
cd /Users/Apple/FormulationOS
find . -name "*formulation*" -type d | head -10
```

应该看到：
- `./src/formulation_os/tools/builtins/formulation_ai/`
- `./assets/formulation_dt/`

### 检查 PreFormulation
```bash
ls -lh /path/to/runner/files/
```

应该看到：
- 模型文件（.pkl, .h5, .pt等）
- 配置文件
- 数据文件

---

## ⚠️ 常见问题

### 问题1: 分卷解压失败
**症状**: macOS自带解压工具无法识别分卷

**解决方案**:
1. 安装第三方解压工具（The Unarchiver或Keka）
2. 确保两个文件（.z01和.zip）在同一目录
3. 使用工具打开.zip文件

### 问题2: 文件路径不确定
**检查runner目录位置**:
```bash
find ~ -name "runner" -type d 2>/dev/null | grep -v ".git"
```

### 问题3: 权限问题
```bash
chmod -R 755 /path/to/files/
```

---

## 🚀 集成后需要更新的代码

### 更新模型路径
如果需要在代码中引用这些模型，可能需要更新：

**FormulationOS_Enterprise.py**
```python
# 添加模型路径配置
FORMULATION_AI_MODEL_PATH = "assets/formulation_dt/"
PREFORMULATION_MODEL_PATH = "runner/files/"
```

**tool配置文件**
```python
# src/formulation_os/tools/builtins/formulation_ai/tool.py
model_path = os.path.join(os.getcwd(), "assets", "formulation_dt")
```

---

## 📝 下一步操作

集成完成后：
1. ✅ 测试FormulationAI工具是否能加载模型
2. ✅ 测试PreFormulation工具是否能访问数据
3. ✅ 更新requirements.txt（如需要新的依赖）
4. ✅ 提交模型文件到Git LFS（如文件很大）

---

## 💾 数据备份建议

这些模型文件很重要，建议：
1. 保留原始压缩包在安全位置
2. 集成后创建完整备份
3. 使用Git LFS管理大文件（>100MB）

**备份命令**:
```bash
# 备份到桌面
mkdir -p ~/Desktop/FormulationOS_Models_Backup
cp -r assets/ ~/Desktop/FormulationOS_Models_Backup/
cp -r runner/files/ ~/Desktop/FormulationOS_Models_Backup/
```

---

## 📞 需要帮助？

如果遇到问题：
1. 检查文件完整性（文件大小、MD5）
2. 确认解压工具支持分卷压缩
3. 查看系统日志获取详细错误信息

**获取文件信息**:
```bash
ls -lh "/Users/Apple/Desktop/FormulationOS/"
file "PreFormulation Files.zip"
```
