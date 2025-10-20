"""用户注册页面"""

import os
import tempfile
import hashlib
import streamlit as st
import soundfile as sf
from voice_gate.config import ENROLLMENT_SAMPLES_COUNT
from voice_gate.audio_processor import embed_audio, save_audio_sample, calculate_prototype
from voice_gate.database import create_user, save_db


def render_enrollment_page(db):
    """
    渲染用户注册页面
    
    Args:
        db: 数据库字典
    """
    # 页面头部
    st.markdown("### 👤 用户注册")
    st.markdown("通过录制语音样本建立用户声纹档案，用于后续身份验证")
    st.markdown("")
    
    # 初始化注册成功标志
    if "registration_success" not in st.session_state:
        st.session_state.registration_success = False
    
    # 如果刚注册成功，显示提示并清空标志
    if st.session_state.registration_success:
        st.success("✅ 用户注册成功！您可以继续注册其他用户或前往验证页面测试。")
        st.session_state.registration_success = False
    
    # 输入区域
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        user_id = st.text_input(
            "用户ID",
            placeholder="请输入用户唯一标识，如：张三、user001",
            help="用户ID将用于识别和管理声纹数据",
            key="enrollment_user_id"
        )
    with col2:
        st.markdown("")
        st.markdown("")
        st.info(f"📝 需要 **{ENROLLMENT_SAMPLES_COUNT}** 个样本")
    with col3:
        st.markdown("")
        st.markdown("")
        if user_id and user_id in db:
            st.warning("⚠️ 已存在")
        elif user_id:
            st.success("✅ 可用")
    
    if user_id:
        # 如果用户已存在，显示提示
        if user_id in db:
            st.warning("⚠️ 该用户ID已存在，请使用其他ID或前往数据库管理页面删除现有用户。")
        else:
            _render_enrollment_process(user_id, db)


def _render_enrollment_process(user_id, db):
    """渲染录制流程"""
    st.markdown("---")
    
    # 进度指示
    st.markdown("#### 📊 录制进度")
    current_progress = len(st.session_state.enrollment_samples)
    progress_percentage = current_progress / ENROLLMENT_SAMPLES_COUNT
    
    col_prog1, col_prog2 = st.columns([4, 1])
    with col_prog1:
        st.progress(progress_percentage)
    with col_prog2:
        st.markdown(f"**{current_progress}/{ENROLLMENT_SAMPLES_COUNT}** 完成")
    
    st.markdown("")
    
    # 样本录制区
    st.markdown("#### 🎙️ 语音样本录制")
    _render_sample_recorders(user_id)
    
    # 注册按钮区
    st.markdown("---")
    _render_submit_button(user_id, db)


def _render_sample_recorders(user_id):
    """渲染录音组件"""
    cols = st.columns(ENROLLMENT_SAMPLES_COUNT)
    
    for i in range(ENROLLMENT_SAMPLES_COUNT):
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
                audio_value = st.audio_input(
                    f"录制语音", 
                    key=f"enroll_{i}", 
                    label_visibility="collapsed"
                )
                
                if audio_value:
                    _process_audio_sample(audio_value, user_id, i)


def _process_audio_sample(audio_value, user_id, sample_index):
    """处理录制的音频样本"""
    # 获取音频哈希值，避免重复处理
    audio_bytes = audio_value.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    # 只处理新音频
    if st.session_state.enrollment_audio_hashes[sample_index] != audio_hash:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # 读取音频
            audio_data, sr = sf.read(tmp_path)
            
            st.audio(audio_value)
            
            # 显示音频信息
            duration = len(audio_data) / sr
            col_a, col_b = st.columns(2)
            with col_a:
                st.caption(f"⏱️ {duration:.1f}s")
            with col_b:
                st.caption(f"📊 {sr}Hz")
            
            # 提取特征
            with st.spinner("分析中..."):
                embedding = embed_audio(audio_data, sr)
            
            # 保存音频文件
            saved_path = save_audio_sample(user_id, audio_data, sr, sample_index + 1)
            
            # 存储到session state
            if len(st.session_state.enrollment_samples) <= sample_index:
                st.session_state.enrollment_samples.append(embedding)
                st.session_state.enrollment_audio_files.append(saved_path)
            else:
                st.session_state.enrollment_samples[sample_index] = embedding
                st.session_state.enrollment_audio_files[sample_index] = saved_path
            
            # 记录哈希值
            st.session_state.enrollment_audio_hashes[sample_index] = audio_hash
            
            os.unlink(tmp_path)
            
            # 立即重新渲染以更新状态
            st.rerun()
            
        except Exception as e:
            st.error(f"处理失败: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        # 已处理过的音频
        st.audio(audio_value)
        if len(st.session_state.enrollment_samples) > sample_index:
            st.caption(f"✅ 已保存")


def _render_submit_button(user_id, db):
    """渲染提交注册按钮"""
    if len(st.session_state.enrollment_samples) == ENROLLMENT_SAMPLES_COUNT:
        st.markdown("#### ✨ 准备完成")
        st.success("所有语音样本已录制完成，可以提交注册了")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 提交注册", type="primary", use_container_width=True):
                with st.spinner("🔄 正在生成声纹模型并保存数据..."):
                    # 计算原型向量
                    prototype = calculate_prototype(st.session_state.enrollment_samples)
                    
                    # 创建用户记录
                    db[user_id] = create_user(
                        user_id, 
                        prototype, 
                        st.session_state.enrollment_audio_files
                    )
                    save_db(db)
                
                st.balloons()
                st.success(f"🎉 恭喜！用户 **{user_id}** 注册成功")
                
                # 清空session state
                st.session_state.enrollment_samples = []
                st.session_state.enrollment_audio_files = []
                st.session_state.enrollment_audio_hashes = [None] * ENROLLMENT_SAMPLES_COUNT
                st.session_state.registration_success = True
                
                # 等待一下让用户看到成功消息，然后重新加载
                st.rerun()
    else:
        remaining = ENROLLMENT_SAMPLES_COUNT - len(st.session_state.enrollment_samples)
        st.info(f"📝 还需录制 **{remaining}** 个语音样本才能完成注册")
