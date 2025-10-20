import os
import pickle
import tempfile
import streamlit as st
import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cdist
from datetime import datetime

DB_PATH = "voice_db.pkl"
AUDIO_DIR = "audio_samples"  # 存储录音文件的目录

# 确保音频目录存在
os.makedirs(AUDIO_DIR, exist_ok=True)

# 初始化语音编码器（使用缓存避免重复加载）
@st.cache_resource(show_spinner="正在加载语音识别模型，请稍候...")
def get_encoder():
    return VoiceEncoder()

# 预加载模型（应用启动时就加载）
with st.spinner("正在初始化语音识别引擎..."):
    encoder = get_encoder()

def embed_audio(audio_data, sr):
    """从音频数据提取特征向量"""
    # 如果采样率不是16kHz，需要重采样（resemblyzer需要16kHz）
    if sr != 16000:
        # 简单重采样（实际应用中可能需要更专业的重采样）
        audio_data = preprocess_wav(audio_data, source_sr=sr)
    else:
        audio_data = preprocess_wav(audio_data)
    return encoder.embed_utterance(audio_data).astype(np.float32)

def save_audio_sample(user_id, audio_data, sr, sample_index):
    """保存音频样本到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{sample_index}_{timestamp}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)
    sf.write(filepath, audio_data, sr)
    return filepath

def load_db():
    """加载用户数据库"""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            db = pickle.load(f)
            # 兼容旧版数据库（如果是旧格式，转换为新格式）
            if db and isinstance(list(db.values())[0], np.ndarray):
                # 旧格式：{user_id: embedding}
                # 转换为新格式：{user_id: {"embedding": embedding, "samples": []}}
                new_db = {}
                for user_id, embedding in db.items():
                    new_db[user_id] = {
                        "embedding": embedding,
                        "samples": [],
                        "created_at": datetime.now().isoformat()
                    }
                return new_db
            return db
    return {}

def save_db(db):
    """保存用户数据库"""
    with open(DB_PATH, "wb") as f:
        pickle.dump(db, f)

st.title("🎙️ Voice Gate - 声纹识别系统")

# 侧边栏：选择模式
mode = st.sidebar.radio("选择模式", ["注册用户", "验证身份", "查看数据库"])

# 加载数据库
db = load_db()

if mode == "注册用户":
    st.header("👤 注册新用户")
    
    user_id = st.text_input("输入用户ID")
    
    if user_id:
        st.info(f"正在为用户 '{user_id}' 注册声纹，请录制 3 段语音样本")
        
        # 初始化session state存储录音
        if "enrollment_samples" not in st.session_state:
            st.session_state.enrollment_samples = []
        if "enrollment_audio_files" not in st.session_state:
            st.session_state.enrollment_audio_files = []
        
        # 录制3段语音
        for i in range(3):
            st.subheader(f"样本 {i+1}/3")
            audio_value = st.audio_input(f"录制样本 {i+1}", key=f"enroll_{i}")
            
            if audio_value:
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_value.read())
                    tmp_path = tmp_file.name
                
                try:
                    # 读取音频
                    audio_data, sr = sf.read(tmp_path)
                    st.audio(audio_value)
                    st.success(f"✅ 样本 {i+1} 录制成功 (时长: {len(audio_data)/sr:.2f}秒)")
                    
                    # 提取特征
                    with st.spinner("正在分析声纹特征..."):
                        embedding = embed_audio(audio_data, sr)
                    
                    # 保存音频文件
                    saved_path = save_audio_sample(user_id, audio_data, sr, i+1)
                    
                    # 存储到session state
                    if len(st.session_state.enrollment_samples) <= i:
                        st.session_state.enrollment_samples.append(embedding)
                        st.session_state.enrollment_audio_files.append(saved_path)
                    else:
                        st.session_state.enrollment_samples[i] = embedding
                        st.session_state.enrollment_audio_files[i] = saved_path
                    
                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"处理音频时出错: {e}")
                    os.unlink(tmp_path)
        
        # 注册按钮
        if len(st.session_state.enrollment_samples) == 3:
            if st.button("完成注册"):
                # 计算原型向量（3个样本的平均值）
                prototype = np.mean(np.stack(st.session_state.enrollment_samples), axis=0)
                db[user_id] = {
                    "embedding": prototype,
                    "samples": st.session_state.enrollment_audio_files.copy(),
                    "created_at": datetime.now().isoformat()
                }
                save_db(db)
                st.success(f"🎉 用户 '{user_id}' 注册成功！")
                st.session_state.enrollment_samples = []
                st.session_state.enrollment_audio_files = []
                st.rerun()
        else:
            st.warning(f"请完成所有 3 段语音样本的录制 (当前: {len(st.session_state.enrollment_samples)}/3)")

elif mode == "验证身份":
    st.header("🔐 验证身份")
    
    if not db:
        st.warning("⚠️ 数据库为空，请先注册用户")
    else:
        st.info("请录制一段语音进行身份验证")
        
        threshold = st.slider("相似度阈值", 0.0, 1.0, 0.75, 0.05)
        
        audio_value = st.audio_input("录制验证语音")
        
        if audio_value:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_value.read())
                tmp_path = tmp_file.name
            
            try:
                # 读取音频
                audio_data, sr = sf.read(tmp_path)
                st.audio(audio_value)
                
                # 提取特征并验证
                with st.spinner("正在分析声纹特征并验证身份..."):
                    probe = embed_audio(audio_data, sr).reshape(1, -1)
                    
                    # 与数据库中所有用户比较
                    keys = list(db.keys())
                    mats = np.stack([db[k]["embedding"] if isinstance(db[k], dict) else db[k] for k in keys], axis=0)
                    sims = 1 - cdist(probe, mats, metric="cosine")[0]
                
                # 找到最匹配的用户
                best_i = np.argmax(sims)
                matched_user = keys[best_i]
                similarity = sims[best_i]
                
                st.subheader("验证结果")
                st.write(f"**最匹配用户**: {matched_user}")
                st.write(f"**相似度**: {similarity:.3f}")
                
                if similarity >= threshold:
                    st.success(f"🟢 验证通过！欢迎 {matched_user}")
                else:
                    st.error("🔴 验证失败！未找到匹配用户")
                
                # 显示所有用户的相似度
                st.subheader("所有用户相似度")
                for user, sim in zip(keys, sims):
                    st.write(f"- {user}: {sim:.3f}")
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"处理音频时出错: {e}")
                os.unlink(tmp_path)

elif mode == "查看数据库":
    st.header("📊 用户数据库管理")
    
    if not db:
        st.info("数据库为空，请先注册用户")
    else:
        st.write(f"**已注册用户数**: {len(db)}")
        st.divider()
        
        # 遍历每个用户
        for user_id in list(db.keys()):
            user_data = db[user_id]
            
            # 使用expander显示用户详情
            with st.expander(f"👤 {user_id}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 显示用户基本信息
                    if isinstance(user_data, dict):
                        st.write(f"**注册时间**: {user_data.get('created_at', '未知')}")
                        st.write(f"**录音样本数**: {len(user_data.get('samples', []))}")
                    else:
                        st.write("**数据格式**: 旧版本（仅包含声纹特征）")
                
                with col2:
                    # 删除用户按钮
                    if st.button("🗑️ 删除用户", key=f"del_{user_id}"):
                        # 删除音频文件
                        if isinstance(user_data, dict) and "samples" in user_data:
                            for audio_path in user_data["samples"]:
                                if os.path.exists(audio_path):
                                    os.remove(audio_path)
                        
                        # 删除数据库记录
                        del db[user_id]
                        save_db(db)
                        st.success(f"已删除用户 {user_id}")
                        st.rerun()
                
                # 显示录音样本
                if isinstance(user_data, dict) and "samples" in user_data and user_data["samples"]:
                    st.subheader("🎵 录音样本")
                    
                    for idx, audio_path in enumerate(user_data["samples"], 1):
                        if os.path.exists(audio_path):
                            col_audio, col_delete = st.columns([4, 1])
                            
                            with col_audio:
                                st.write(f"**样本 {idx}**: {os.path.basename(audio_path)}")
                                st.audio(audio_path)
                            
                            with col_delete:
                                st.write("")  # 空行对齐
                                if st.button("🗑️", key=f"del_audio_{user_id}_{idx}"):
                                    # 删除音频文件
                                    os.remove(audio_path)
                                    
                                    # 从数据库中移除
                                    user_data["samples"].remove(audio_path)
                                    save_db(db)
                                    
                                    st.success(f"已删除样本 {idx}")
                                    st.rerun()
                        else:
                            st.warning(f"样本 {idx}: 文件不存在 ({audio_path})")
                    
                    # 添加新录音样本
                    st.subheader("➕ 添加新样本")
                    new_audio = st.audio_input(f"为 {user_id} 录制新样本", key=f"add_audio_{user_id}")
                    
                    if new_audio:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            tmp_file.write(new_audio.read())
                            tmp_path = tmp_file.name
                        
                        try:
                            with st.spinner("正在处理新样本并更新声纹特征..."):
                                # 读取音频
                                audio_data, sr = sf.read(tmp_path)
                                
                                # 保存音频文件
                                next_index = len(user_data["samples"]) + 1
                                saved_path = save_audio_sample(user_id, audio_data, sr, next_index)
                                
                                # 提取特征并更新原型向量
                                new_embedding = embed_audio(audio_data, sr)
                                
                                # 重新计算原型向量（所有样本的平均值）
                                all_embeddings = [new_embedding]
                                for sample_path in user_data["samples"]:
                                    if os.path.exists(sample_path):
                                        sample_audio, sample_sr = sf.read(sample_path)
                                        all_embeddings.append(embed_audio(sample_audio, sample_sr))
                                
                                user_data["embedding"] = np.mean(np.stack(all_embeddings), axis=0)
                                user_data["samples"].append(saved_path)
                                save_db(db)
                            
                            os.unlink(tmp_path)
                            st.success(f"✅ 新样本已添加并更新声纹特征")
                            st.rerun()
                        except Exception as e:
                            st.error(f"处理音频时出错: {e}")
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                else:
                    st.info("该用户无录音样本（可能是旧版本数据）")
                
                st.divider()

