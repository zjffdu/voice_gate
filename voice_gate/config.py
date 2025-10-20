"""配置文件"""

import os

# 数据库配置
DB_PATH = "voice_db.pkl"
AUDIO_DIR = "audio_samples"

# 模型配置
MODEL_SAMPLE_RATE = 16000
EMBEDDING_DIM = 256

# 录音配置
MIN_DURATION = 1.0  # 最短录音时长（秒）
MAX_DURATION = 10.0  # 最长录音时长（秒）
OPTIMAL_MIN_DURATION = 2.0  # 最佳最短时长（秒）
OPTIMAL_MAX_DURATION = 5.0  # 最佳最长时长（秒）
ENROLLMENT_SAMPLES_COUNT = 3  # 注册所需样本数

# 验证配置
DEFAULT_THRESHOLD = 0.75  # 默认验证阈值

# 确保必要的目录存在
os.makedirs(AUDIO_DIR, exist_ok=True)
