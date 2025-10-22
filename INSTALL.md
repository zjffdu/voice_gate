## 💻 运行环境

### 硬件要求
- **CPU**：Intel i5 或以上（推荐 i7）
- **内存**：4GB RAM 以上（推荐 8GB）
- **存储**：500MB 可用空间
- **麦克风**：任何标准麦克风设备

### 软件环境

#### 操作系统
- ✅ macOS 10.15+
- ✅ Windows 10/11
- ✅ Linux (Ubuntu 20.04+)

#### Python 环境
- **Python 版本**：≥ 3.10
- **包管理器**：uv（推荐）或 pip

#### 核心依赖库

| 库名 | 版本 | 用途 |
|------|------|------|
| **streamlit** | ≥1.50.0 | Web 界面框架 |
| **resemblyzer** | ≥0.1.4 | 声纹特征提取（基于 PyTorch） |
| **numpy** | ≥1.21.0 | 数值计算 |
| **scipy** | ≥1.7.0 | 科学计算（余弦距离） |
| **soundfile** | ≥0.13.1 | 音频文件 I/O |

### 安装步骤

#### 方式一：使用 uv（推荐）
```bash
# 1. 使用 uv 安装依赖
uv sync

# 2. 运行应用
uv run streamlit run app.py
```

#### 方式二：使用 pip
```bash

# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install streamlit>=1.50.0 resemblyzer numpy scipy soundfile

# 3. 运行应用
streamlit run app.py
```

### 浏览器要求
- **推荐**：Chrome 90+, Edge 90+, Safari 14+