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

# 页面配置
st.set_page_config(
    page_title="Voice Gate - 声纹识别系统",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    /* 卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .info-card {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* 按钮样式优化 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    /* Tab样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8fafc;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    
    /* 成功/错误消息样式 */
    .stSuccess {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
    }
    
    .stError {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<h1 class="main-header">🎙️ Voice Gate</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">企业级声纹识别与身份验证平台</p>', unsafe_allow_html=True)

# 加载数据库
db = load_db()

# 在侧边栏显示统计信息
with st.sidebar:
    st.markdown("### 📊 系统概览")
    st.markdown("")
    
    # 统计卡片
    total_users = len(db)
    total_samples = sum(len(user_data.get("samples", [])) if isinstance(user_data, dict) else 0 for user_data in db.values())
    avg_samples = total_samples / total_users if total_users > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="👥 用户数",
            value=total_users,
            delta=None
        )
    with col2:
        st.metric(
            label="🎵 样本数",
            value=total_samples,
            delta=None
        )
    
    st.markdown("---")
    
    # 系统信息
    st.markdown("### ⚙️ 系统信息")
    st.markdown(f"""
    - **模型状态**: <span style='color: #10b981;'>● 运行中</span>
    - **编码器**: Resemblyzer
    - **采样率**: 16kHz
    - **特征维度**: 256
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 使用指南
    with st.expander("💡 使用指南", expanded=False):
        st.markdown("""
        **注册用户**
        - 输入唯一的用户ID
        - 录制3段清晰语音
        - 每段建议2-5秒
        
        **身份验证**
        - 录制一段语音
        - 系统自动识别
        - 调整阈值控制精度
        
        **最佳实践**
        - 保持环境安静
        - 使用相同设备
        - 正常音量说话
        """)
    
    st.markdown("---")
    st.caption("Powered by Resemblyzer · v1.0.0")

# 初始化所有需要的session state（在tabs之前，避免第一次切换tab时的状态初始化导致页面跳转）
if "verification_counter" not in st.session_state:
    st.session_state.verification_counter = 0
if "enrollment_samples" not in st.session_state:
    st.session_state.enrollment_samples = []
if "enrollment_audio_files" not in st.session_state:
    st.session_state.enrollment_audio_files = []
if "enrollment_audio_hashes" not in st.session_state:
    st.session_state.enrollment_audio_hashes = [None, None, None]  # 跟踪每个样本的哈希值

# 使用tabs替代radio
tab1, tab2, tab3 = st.tabs(["👤 注册用户", "🔐 验证身份", "📊 数据库管理"])

with tab1:
    # 页面头部
    st.markdown("### 👤 用户注册")
    st.markdown("通过录制语音样本建立用户声纹档案，用于后续身份验证")
    st.markdown("")
    
    # 输入区域
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        user_id = st.text_input(
            "用户ID",
            placeholder="请输入用户唯一标识，如：张三、user001",
            help="用户ID将用于识别和管理声纹数据"
        )
    with col2:
        st.markdown("")
        st.markdown("")
        st.info("📝 需要 **3** 个样本")
    with col3:
        st.markdown("")
        st.markdown("")
        if user_id and user_id in db:
            st.warning("⚠️ 已存在")
        elif user_id:
            st.success("✅ 可用")
    
    if user_id:
        st.markdown("---")
        
        # 进度指示区
        with st.container():
            st.markdown("#### 📊 录制进度")
        
        # 录制3段语音
        current_progress = len(st.session_state.enrollment_samples)
        progress_percentage = current_progress / 3
        
        col_prog1, col_prog2 = st.columns([4, 1])
        with col_prog1:
            st.progress(progress_percentage)
        with col_prog2:
            st.markdown(f"**{current_progress}/3** 完成")
        
        st.markdown("")
        
        # 样本录制区
        st.markdown("#### 🎙️ 语音样本录制")
        
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                with st.container(border=True):
                    # 状态标识
                    if len(st.session_state.enrollment_samples) > i:
                        st.markdown(f"##### ✅ 样本 {i+1}")
                        st.markdown('<div style="color: #10b981; font-weight: 500;">已完成</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"##### 📝 样本 {i+1}")
                        st.markdown('<div style="color: #f59e0b; font-weight: 500;">待录制</div>', unsafe_allow_html=True)
                    
                    st.markdown("")
                    audio_value = st.audio_input(f"录制语音", key=f"enroll_{i}", label_visibility="collapsed")
                
                    if audio_value:
                        # 获取音频的哈希值，避免重复处理同一个音频
                        import hashlib
                        audio_bytes = audio_value.getvalue()
                        audio_hash = hashlib.md5(audio_bytes).hexdigest()
                        
                        # 只有当这是新的音频时才处理
                        if st.session_state.enrollment_audio_hashes[i] != audio_hash:
                            # 保存到临时文件
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_path = tmp_file.name
                        
                            try:
                                # 读取音频
                                audio_data, sr = sf.read(tmp_path)
                                
                                st.audio(audio_value)
                                
                                # 显示音频信息
                                duration = len(audio_data)/sr
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.caption(f"⏱️ {duration:.1f}s")
                                with col_b:
                                    st.caption(f"📊 {sr}Hz")
                                
                                # 提取特征
                                with st.spinner("分析中..."):
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
                                
                                # 记录此音频的哈希值
                                st.session_state.enrollment_audio_hashes[i] = audio_hash
                                
                                os.unlink(tmp_path)
                                
                                # 立即重新渲染以更新状态显示
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"处理失败: {e}")
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                        else:
                            # 已经处理过这个音频，只显示播放器
                            st.audio(audio_value)
                            if len(st.session_state.enrollment_samples) > i:
                                st.caption(f"✅ 已保存")
        
        # 注册按钮区
        st.markdown("---")
        
        if len(st.session_state.enrollment_samples) == 3:
            st.markdown("#### ✨ 准备完成")
            st.success("所有语音样本已录制完成，可以提交注册了")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 提交注册", type="primary", use_container_width=True):
                    with st.spinner("🔄 正在生成声纹模型并保存数据..."):
                        # 计算原型向量（3个样本的平均值）
                        prototype = np.mean(np.stack(st.session_state.enrollment_samples), axis=0)
                        db[user_id] = {
                            "embedding": prototype,
                            "samples": st.session_state.enrollment_audio_files.copy(),
                            "created_at": datetime.now().isoformat()
                        }
                        save_db(db)
                    st.balloons()
                    st.success(f"🎉 恭喜！用户 **{user_id}** 注册成功")
                    st.session_state.enrollment_samples = []
                    st.session_state.enrollment_audio_files = []
                    st.rerun()
        else:
            remaining = 3 - len(st.session_state.enrollment_samples)
            st.info(f"📝 还需录制 **{remaining}** 个语音样本才能完成注册")

with tab2:
    # 页面头部
    st.markdown("### 🔐 身份验证")
    st.markdown("录制一段语音，系统将通过声纹识别技术自动验证您的身份")
    st.markdown("")
    
    if not db:
        st.warning("⚠️ 系统中暂无注册用户，请先在「用户注册」页面添加用户")
    else:
        # 配置区域
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.metric(
                    label="� 注册用户数",
                    value=len(db),
                    help="当前系统中已注册的用户总数"
                )
            with col2:
                st.metric(
                    label="🎵 声纹样本库",
                    value=sum(len(user_data.get("samples", [])) if isinstance(user_data, dict) else 0 for user_data in db.values()),
                    help="所有用户的语音样本总数"
                )
            with col3:
                threshold = st.slider(
                    "🎯 识别阈值",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.75,
                    step=0.05,
                    help="相似度阈值：值越高验证越严格，降低误识率但可能增加拒识率"
                )
        
        st.markdown("---")
        
        # 录音区域
        st.markdown("#### 🎙️ 语音录制")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # 使用counter作为key的一部分，确保每次重置时创建新的组件
            audio_value = st.audio_input(
                "点击麦克风按钮开始录制", 
                label_visibility="collapsed", 
                key=f"verify_audio_{st.session_state.verification_counter}"
            )
        
        with col_right:
            st.markdown("")
            st.markdown("")
            st.info("💡 **录音建议**\n\n清晰发音 · 2-5秒 · 安静环境")
        
        if audio_value:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_value.read())
                tmp_path = tmp_file.name
            
            try:
                st.markdown("---")
                st.markdown("#### 🔍 分析结果")
                
                # 读取音频
                audio_data, sr = sf.read(tmp_path)
                
                # 显示音频播放器
                with st.container():
                    col_play, col_info1, col_info2 = st.columns([3, 1, 1])
                    with col_play:
                        st.audio(audio_value)
                    with col_info1:
                        st.metric("⏱️ 时长", f"{len(audio_data)/sr:.1f}s")
                    with col_info2:
                        st.metric("📊 采样率", f"{sr}Hz")
                
                # 提取特征并验证
                with st.spinner("� 正在进行声纹特征提取与匹配分析..."):
                    probe = embed_audio(audio_data, sr).reshape(1, -1)
                    
                    # 与数据库中所有用户比较
                    keys = list(db.keys())
                    mats = np.stack([db[k]["embedding"] if isinstance(db[k], dict) else db[k] for k in keys], axis=0)
                    sims = 1 - cdist(probe, mats, metric="cosine")[0]
                
                # 找到最匹配的用户
                best_i = np.argmax(sims)
                matched_user = keys[best_i]
                similarity = sims[best_i]
                
                st.markdown("")
                
                # 验证结果展示
                if similarity >= threshold:
                    # 验证通过
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                                padding: 2rem; border-radius: 12px; border-left: 5px solid #10b981;'>
                        <h2 style='color: #065f46; margin: 0;'>✅ 验证通过</h2>
                        <p style='color: #047857; font-size: 1.2rem; margin-top: 0.5rem;'>
                            身份确认成功，欢迎回来！
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👤 识别用户", matched_user)
                    with col2:
                        st.metric("📊 匹配度", f"{similarity:.1%}", delta=f"+{(similarity-threshold)*100:.1f}%")
                    with col3:
                        st.metric("🎯 阈值", f"{threshold:.1%}")
                    
                else:
                    # 验证失败
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                                padding: 2rem; border-radius: 12px; border-left: 5px solid #ef4444;'>
                        <h2 style='color: #991b1b; margin: 0;'>❌ 验证失败</h2>
                        <p style='color: #dc2626; font-size: 1.2rem; margin-top: 0.5rem;'>
                            声纹匹配度不足，身份验证未通过
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("👤 最接近用户", matched_user)
                    with col2:
                        st.metric("📊 匹配度", f"{similarity:.1%}", delta=f"{(similarity-threshold)*100:.1f}%", delta_color="inverse")
                    with col3:
                        st.metric("🎯 阈值", f"{threshold:.1%}")
                
                # 详细匹配结果
                st.markdown("")
                with st.expander("📊 查看所有用户匹配详情", expanded=False):
                    st.markdown("##### 匹配度排行")
                    
                    # 排序显示
                    sorted_indices = np.argsort(sims)[::-1]
                    for rank, idx in enumerate(sorted_indices, 1):
                        user = keys[idx]
                        sim = sims[idx]
                        
                        # 排名标识
                        if rank == 1:
                            rank_badge = "🥇"
                            rank_color = "#fbbf24"
                        elif rank == 2:
                            rank_badge = "🥈"
                            rank_color = "#9ca3af"
                        elif rank == 3:
                            rank_badge = "🥉"
                            rank_color = "#d97706"
                        else:
                            rank_badge = f"{rank}"
                            rank_color = "#6b7280"
                        
                        # 状态标识
                        status = "✅ 通过" if sim >= threshold else "❌ 未通过"
                        status_color = "#10b981" if sim >= threshold else "#ef4444"
                        
                        col_a, col_b, col_c = st.columns([1, 3, 1])
                        with col_a:
                            st.markdown(f"<div style='font-size: 1.5rem;'>{rank_badge}</div>", unsafe_allow_html=True)
                        with col_b:
                            st.markdown(f"**{user}**")
                            st.progress(sim, text=f"{sim:.1%}")
                        with col_c:
                            st.markdown(f"<div style='color: {status_color}; font-weight: 600;'>{status}</div>", unsafe_allow_html=True)
                
                # 添加重新验证按钮
                st.markdown("")
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 进行新的验证", type="primary", use_container_width=True, key="new_verify_bottom"):
                        st.session_state.verification_counter += 1  # 增加计数器，强制重新创建录音组件
                        st.rerun()
                
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"处理音频时出错: {e}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

with tab3:
    # 页面头部
    st.markdown("### 📊 数据库管理")
    st.markdown("管理用户声纹数据，支持查看、编辑和删除操作")
    st.markdown("")
    
    if not db:
        # 空状态展示
        st.markdown("""
        <div style='text-align: center; padding: 4rem 2rem; background: #f8fafc; border-radius: 12px;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>📭</div>
            <h3 style='color: #64748b;'>数据库为空</h3>
            <p style='color: #94a3b8;'>暂无注册用户，请前往「用户注册」页面添加用户</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 统计仪表板
        st.markdown("#### 📈 数据统计")
        
        total_samples = sum(len(user_data.get("samples", [])) if isinstance(user_data, dict) else 0 for user_data in db.values())
        avg_samples = total_samples / len(db) if len(db) > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 12px; color: white;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>👥</div>
                <div style='font-size: 2rem; font-weight: 700;'>{}</div>
                <div style='opacity: 0.9;'>注册用户</div>
            </div>
            """.format(len(db)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 1.5rem; border-radius: 12px; color: white;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🎵</div>
                <div style='font-size: 2rem; font-weight: 700;'>{}</div>
                <div style='opacity: 0.9;'>语音样本</div>
            </div>
            """.format(total_samples), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 1.5rem; border-radius: 12px; color: white;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📊</div>
                <div style='font-size: 2rem; font-weight: 700;'>{:.1f}</div>
                <div style='opacity: 0.9;'>平均样本</div>
            </div>
            """.format(avg_samples), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 1.5rem; border-radius: 12px; color: white;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>💾</div>
                <div style='font-size: 2rem; font-weight: 700;'>256</div>
                <div style='opacity: 0.9;'>特征维度</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("---")
        st.markdown("#### 👥 用户列表")
        
        # 遍历每个用户
        for idx, user_id in enumerate(list(db.keys()), 1):
            user_data = db[user_id]
            
            # 使用expander显示用户详情
            with st.expander(f"👤 {user_id}", expanded=False):
                # 用户信息头部
                if isinstance(user_data, dict):
                    created_time = user_data.get('created_at', '未知')
                    if created_time != '未知':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_time)
                            created_time = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # 信息卡片
                    col_info1, col_info2, col_action = st.columns([2, 2, 1])
                    
                    with col_info1:
                        st.markdown(f"""
                        <div style='background: #f8fafc; padding: 1rem; border-radius: 8px;'>
                            <div style='color: #64748b; font-size: 0.875rem;'>📅 注册时间</div>
                            <div style='color: #1e293b; font-weight: 600; margin-top: 0.25rem;'>{created_time}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_info2:
                        sample_count = len(user_data.get('samples', []))
                        st.markdown(f"""
                        <div style='background: #f8fafc; padding: 1rem; border-radius: 8px;'>
                            <div style='color: #64748b; font-size: 0.875rem;'>🎵 语音样本</div>
                            <div style='color: #1e293b; font-weight: 600; margin-top: 0.25rem;'>{sample_count} 个</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_action:
                        st.markdown("")
                        # 删除用户按钮
                        if st.button("🗑️ 删除用户", key=f"del_{user_id}", type="secondary", use_container_width=True):
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
                else:
                    st.info("ℹ️ 旧版本数据（仅包含声纹特征）")
                
                st.markdown("")
                
                # 显示录音样本
                if isinstance(user_data, dict) and "samples" in user_data:
                    if user_data["samples"]:
                        st.markdown("##### 🎵 语音样本库")
                        st.markdown("")
                        
                        # 使用列布局展示样本
                        cols_per_row = 3
                        for i in range(0, len(user_data["samples"]), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                idx_sample = i + j
                                if idx_sample < len(user_data["samples"]):
                                    audio_path = user_data["samples"][idx_sample]
                                    with col:
                                        with st.container(border=True):
                                            if os.path.exists(audio_path):
                                                st.markdown(f"**样本 {idx_sample + 1}**")
                                                st.audio(audio_path)
                                                st.caption(f"`{os.path.basename(audio_path)}`")
                                                
                                                if st.button("🗑️ 删除", key=f"del_audio_{user_id}_{idx_sample}", use_container_width=True):
                                                    # 删除音频文件
                                                    os.remove(audio_path)
                                                    
                                                    # 从数据库中移除
                                                    user_data["samples"].remove(audio_path)
                                                    save_db(db)
                                                    
                                                    st.success(f"✅ 已删除样本 {idx_sample + 1}")
                                                    st.rerun()
                                            else:
                                                st.warning(f"⚠️ 文件不存在")
                                                st.caption(f"`{os.path.basename(audio_path)}`")
                        
                        st.markdown("")
                    else:
                        st.info("ℹ️ 该用户暂无录音样本")
                    
                    # 添加新录音样本（无论是否有样本都显示）
                    st.markdown("---")
                    st.markdown("##### ➕ 添加新样本")
                    st.markdown("录制新的语音样本以增强识别准确率")
                    
                    col_audio, col_tip = st.columns([3, 1])
                    with col_audio:
                        new_audio = st.audio_input(f"录制新样本", key=f"add_audio_{user_id}", label_visibility="collapsed")
                    with col_tip:
                        st.markdown("")
                        st.markdown("")
                        st.info("💡 建议录制 2-5 秒")
                    
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

