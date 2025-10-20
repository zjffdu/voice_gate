import streamlit as st
import soundfile as sf
import numpy as np
import tempfile
import os

st.title("🎙️ Streamlit 原生录音 Demo")

st.info("点击下方的录音按钮，允许浏览器访问麦克风，然后开始说话。录完后点击停止。")

# 使用 Streamlit 原生录音组件
audio_value = st.audio_input("录制语音")

if audio_value:
    st.success("✅ 录音成功！")
    
    # 显示音频播放器
    st.audio(audio_value)
    
    # 保存音频到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_value.read())
        tmp_path = tmp_file.name
    
    # 读取音频信息
    try:
        audio_data, sample_rate = sf.read(tmp_path)
        
        st.subheader("📊 音频信息")
        st.write(f"- **采样率**: {sample_rate} Hz")
        st.write(f"- **时长**: {len(audio_data) / sample_rate:.2f} 秒")
        st.write(f"- **数据形状**: {audio_data.shape}")
        st.write(f"- **数据类型**: {audio_data.dtype}")
        
        # 显示音频波形的统计信息
        st.write(f"- **音频范围**: [{audio_data.min():.4f}, {audio_data.max():.4f}]")
        st.write(f"- **平均幅度**: {np.abs(audio_data).mean():.4f}")
        
        st.success(f"✅ 音频数据已成功加载，可以用于后续的语音识别或验证！")
        
        # 清理临时文件
        os.unlink(tmp_path)
        
    except Exception as e:
        st.error(f"读取音频时出错: {e}")
        os.unlink(tmp_path)
else:
    st.info("暂无录音。请点击上方的录音按钮开始录制。")

st.divider()
st.caption("💡 提示：此方案使用 Streamlit 原生录音功能，无需 WebRTC，兼容性更好。")
