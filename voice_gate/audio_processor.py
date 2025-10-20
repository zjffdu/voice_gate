"""音频处理和声纹特征提取"""

import os
import numpy as np
import soundfile as sf
import streamlit as st
from resemblyzer import VoiceEncoder, preprocess_wav
from datetime import datetime
from voice_gate.config import MODEL_SAMPLE_RATE, AUDIO_DIR


@st.cache_resource(show_spinner="正在加载语音识别模型，请稍候...")
def get_encoder():
    """获取语音编码器（带缓存）"""
    return VoiceEncoder()


def embed_audio(audio_data, sr):
    """
    从音频数据提取特征向量
    
    Args:
        audio_data: 音频数据数组
        sr: 采样率
    
    Returns:
        np.ndarray: 256维特征向量
    """
    encoder = get_encoder()
    
    # 如果采样率不是16kHz，需要重采样
    if sr != MODEL_SAMPLE_RATE:
        audio_data = preprocess_wav(audio_data, source_sr=sr)
    else:
        audio_data = preprocess_wav(audio_data)
    
    return encoder.embed_utterance(audio_data).astype(np.float32)


def save_audio_sample(user_id, audio_data, sr, sample_index):
    """
    保存音频样本到文件
    
    Args:
        user_id: 用户ID
        audio_data: 音频数据
        sr: 采样率
        sample_index: 样本索引
    
    Returns:
        str: 保存的文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{sample_index}_{timestamp}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)
    sf.write(filepath, audio_data, sr)
    return filepath


def calculate_prototype(embeddings):
    """
    计算原型向量（多个样本的平均值）
    
    Args:
        embeddings: embedding列表
    
    Returns:
        np.ndarray: 原型向量
    """
    return np.mean(np.stack(embeddings), axis=0)
