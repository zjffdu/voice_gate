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
st.markdown("---")

# 加载数据库
db = load_db()

# 在侧边栏显示统计信息
with st.sidebar:
    st.header("📊 系统状态")
    st.metric("已注册用户", len(db))
    if db:
        total_samples = sum(len(user_data.get("samples", [])) if isinstance(user_data, dict) else 0 for user_data in db.values())
        st.metric("录音样本总数", total_samples)
    st.markdown("---")
    st.info("💡 **使用提示**\n\n1. 首次使用请先注册用户\n2. 录音时保持环境安静\n3. 每次录音建议2-5秒\n4. 验证阈值越高越严格")

# 使用tabs替代radio
tab1, tab2, tab3 = st.tabs(["👤 注册用户", "🔐 验证身份", "📊 数据库管理"])

with tab1:
    st.header("👤 注册新用户")
    st.markdown("请输入用户ID并录制3段语音样本来建立声纹档案")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        user_id = st.text_input("用户ID", placeholder="例如：张三、user001等")
    with col2:
        st.metric("需要样本数", "3", help="系统会通过3段语音的平均特征建立更准确的声纹模型")
    
    if user_id:
        st.success(f"✅ 用户ID: **{user_id}**")
        st.markdown("---")
        
        # 初始化session state存储录音
        if "enrollment_samples" not in st.session_state:
            st.session_state.enrollment_samples = []
        if "enrollment_audio_files" not in st.session_state:
            st.session_state.enrollment_audio_files = []
        
        # 录制3段语音
        progress_text = f"录音进度: {len(st.session_state.enrollment_samples)}/3"
        progress = len(st.session_state.enrollment_samples) / 3
        st.progress(progress, text=progress_text)
        st.markdown("")
        
        for i in range(3):
            with st.container(border=True):
                col_title, col_status = st.columns([3, 1])
                with col_title:
                    st.subheader(f"🎤 样本 {i+1}")
                with col_status:
                    if len(st.session_state.enrollment_samples) > i:
                        st.success("✅ 已完成")
                    else:
                        st.warning("⏳ 待录制")
                
                audio_value = st.audio_input(f"点击录制第 {i+1} 段语音", key=f"enroll_{i}")
                
                if audio_value:
                    # 保存到临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_value.read())
                        tmp_path = tmp_file.name
                    
                    try:
                        # 读取音频
                        audio_data, sr = sf.read(tmp_path)
                        
                        col_play, col_info = st.columns([2, 1])
                        with col_play:
                            st.audio(audio_value)
                        with col_info:
                            st.metric("时长", f"{len(audio_data)/sr:.2f}秒")
                        
                        # 提取特征
                        with st.spinner("🔍 正在分析声纹特征..."):
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
                        
                        st.success("✨ 声纹特征提取完成")
                        os.unlink(tmp_path)
                    except Exception as e:
                        st.error(f"❌ 处理音频时出错: {e}")
                        os.unlink(tmp_path)
        
        # 注册按钮
        st.markdown("---")
        if len(st.session_state.enrollment_samples) == 3:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✅ 完成注册", type="primary", use_container_width=True):
                    with st.spinner("正在生成声纹模型..."):
                        # 计算原型向量（3个样本的平均值）
                        prototype = np.mean(np.stack(st.session_state.enrollment_samples), axis=0)
                        db[user_id] = {
                            "embedding": prototype,
                            "samples": st.session_state.enrollment_audio_files.copy(),
                            "created_at": datetime.now().isoformat()
                        }
                        save_db(db)
                    st.balloons()
                    st.success(f"🎉 用户 **{user_id}** 注册成功！")
                    st.session_state.enrollment_samples = []
                    st.session_state.enrollment_audio_files = []
                    st.rerun()
        else:
            st.info(f"📝 请完成所有语音样本的录制 (当前: {len(st.session_state.enrollment_samples)}/3)")

with tab2:
    st.header("🔐 验证身份")
    st.markdown("录制一段语音，系统将自动识别您的身份")
    
    if not db:
        st.warning("⚠️ 数据库为空，请先在「注册用户」页面注册")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"💾 数据库中有 **{len(db)}** 位已注册用户")
        with col2:
            threshold = st.slider("阈值", 0.0, 1.0, 0.75, 0.05, help="相似度阈值，越高越严格")
        
        st.markdown("---")
        audio_value = st.audio_input("🎤 点击录制验证语音")
        
        if audio_value:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_value.read())
                tmp_path = tmp_file.name
            
            try:
                # 读取音频
                audio_data, sr = sf.read(tmp_path)
                
                col_play, col_info = st.columns([2, 1])
                with col_play:
                    st.audio(audio_value)
                with col_info:
                    st.metric("时长", f"{len(audio_data)/sr:.2f}秒")
                
                # 提取特征并验证
                with st.spinner("🔍 正在分析声纹特征并验证身份..."):
                    probe = embed_audio(audio_data, sr).reshape(1, -1)
                    
                    # 与数据库中所有用户比较
                    keys = list(db.keys())
                    mats = np.stack([db[k]["embedding"] if isinstance(db[k], dict) else db[k] for k in keys], axis=0)
                    sims = 1 - cdist(probe, mats, metric="cosine")[0]
                
                # 找到最匹配的用户
                best_i = np.argmax(sims)
                matched_user = keys[best_i]
                similarity = sims[best_i]
                
                st.markdown("---")
                st.subheader("🎯 验证结果")
                
                # 使用大号显示结果
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("最匹配用户", matched_user)
                with col2:
                    st.metric("相似度", f"{similarity:.1%}", delta=f"阈值 {threshold:.1%}")
                
                if similarity >= threshold:
                    st.success(f"✅ **验证通过！** 欢迎回来，{matched_user} 👋")
                else:
                    st.error(f"❌ **验证失败！** 相似度 ({similarity:.1%}) 低于阈值 ({threshold:.1%})")
                
                # 显示所有用户的相似度
                with st.expander("📊 查看详细匹配结果", expanded=False):
                    st.markdown("**所有用户相似度排名：**")
                    # 排序显示
                    sorted_indices = np.argsort(sims)[::-1]
                    for rank, idx in enumerate(sorted_indices, 1):
                        user = keys[idx]
                        sim = sims[idx]
                        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "　"
                        color = "🟢" if sim >= threshold else "🔴"
                        st.write(f"{emoji} **{rank}.** {user}: {color} {sim:.1%}")
                        st.progress(sim)
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"处理音频时出错: {e}")
                os.unlink(tmp_path)

with tab3:
    st.header("📊 数据库管理")
    st.markdown("查看、管理已注册用户的声纹数据")
    
    if not db:
        st.info("📭 数据库为空，请先在「注册用户」页面注册")
    else:
        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 用户总数", len(db))
        with col2:
            total_samples = sum(len(user_data.get("samples", [])) if isinstance(user_data, dict) else 0 for user_data in db.values())
            st.metric("🎵 样本总数", total_samples)
        with col3:
            avg_samples = total_samples / len(db) if len(db) > 0 else 0
            st.metric("📈 平均样本", f"{avg_samples:.1f}")
        
        st.markdown("---")
        
        # 遍历每个用户
        for idx, user_id in enumerate(list(db.keys()), 1):
            user_data = db[user_id]
            
            # 使用expander显示用户详情
            with st.expander(f"👤 **{idx}. {user_id}**", expanded=False):
                # 用户信息卡片
                info_col, action_col = st.columns([3, 1])
                
                with info_col:
                    # 显示用户基本信息
                    if isinstance(user_data, dict):
                        created_time = user_data.get('created_at', '未知')
                        if created_time != '未知':
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(created_time)
                                created_time = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                pass
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"📅 **注册时间**: {created_time}")
                        with col_b:
                            st.markdown(f"🎵 **样本数量**: {len(user_data.get('samples', []))} 个")
                    else:
                        st.info("ℹ️ 旧版本数据（仅包含声纹特征）")
                
                with action_col:
                    # 删除用户按钮
                    if st.button("🗑️ 删除", key=f"del_{user_id}", type="secondary", use_container_width=True):
                        # 删除音频文件
                        if isinstance(user_data, dict) and "samples" in user_data:
                            for audio_path in user_data["samples"]:
                                if os.path.exists(audio_path):
                                    os.remove(audio_path)
                        
                        # 删除数据库记录
                        del db[user_id]
                        save_db(db)
                        st.success(f"✅ 已删除用户 {user_id}")
                        st.rerun()
                
                st.markdown("---")
                
                # 显示录音样本
                if isinstance(user_data, dict) and "samples" in user_data:
                    if user_data["samples"]:
                        st.markdown("##### 🎵 录音样本")
                        
                        for idx, audio_path in enumerate(user_data["samples"], 1):
                            with st.container(border=True):
                                if os.path.exists(audio_path):
                                    col_audio, col_delete = st.columns([5, 1])
                                    
                                    with col_audio:
                                        st.markdown(f"**样本 {idx}** · `{os.path.basename(audio_path)}`")
                                        st.audio(audio_path)
                                    
                                    with col_delete:
                                        if st.button("🗑️", key=f"del_audio_{user_id}_{idx}", help="删除此样本"):
                                            # 删除音频文件
                                            os.remove(audio_path)
                                            
                                            # 从数据库中移除
                                            user_data["samples"].remove(audio_path)
                                            save_db(db)
                                            
                                            st.success(f"✅ 已删除样本 {idx}")
                                            st.rerun()
                                else:
                                    st.warning(f"⚠️ 样本 {idx}: 文件不存在")
                                    st.caption(f"路径: {audio_path}")
                        
                        st.markdown("---")
                    else:
                        st.info("ℹ️ 该用户暂无录音样本")
                    
                    # 添加新录音样本（无论是否有样本都显示）
                    st.markdown("##### ➕ 添加新样本")
                    new_audio = st.audio_input(f"为用户 {user_id} 录制新样本", key=f"add_audio_{user_id}")
                    
                    # 使用session state跟踪已处理的音频，避免重复添加
                    audio_session_key = f"processed_audio_{user_id}"
                    if audio_session_key not in st.session_state:
                        st.session_state[audio_session_key] = None
                    
                    if new_audio:
                        # 获取音频的唯一标识（使用音频数据的哈希值）
                        audio_bytes = new_audio.getvalue()
                        import hashlib
                        audio_hash = hashlib.md5(audio_bytes).hexdigest()
                        
                        # 只有当这是新的音频时才处理
                        if st.session_state[audio_session_key] != audio_hash:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
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
                                    
                                    # 标记这个音频已处理
                                    st.session_state[audio_session_key] = audio_hash
                                
                                os.unlink(tmp_path)
                                st.success(f"✅ 新样本已添加，声纹特征已更新")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 处理音频时出错: {e}")
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                        else:
                            # 音频已处理过，显示提示
                            st.info("ℹ️ 此音频样本已添加，请录制新的音频")
                else:
                    st.info("ℹ️ 该用户数据格式异常（可能是旧版本数据）")

