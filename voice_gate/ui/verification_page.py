"""身份验证页面"""

import os
import tempfile
import streamlit as st
import soundfile as sf
from voice_gate.config import DEFAULT_THRESHOLD
from voice_gate.audio_processor import embed_audio
from voice_gate.verifier import verify_voice, get_similarity_ranking
from voice_gate.ui_styles import SUCCESS_CARD_HTML, FAILURE_CARD_HTML


def render_verification_page(db):
    """
    渲染身份验证页面
    
    Args:
        db: 数据库字典
    """
    st.markdown("### 🔐 身份验证")
    st.markdown("录制一段语音，系统将通过声纹识别技术自动验证您的身份")
    st.markdown("")
    
    if not db:
        st.warning("⚠️ 系统中暂无注册用户，请先在「用户注册」页面添加用户")
        return
    
    # 配置区域
    threshold = _render_config_section(db)
    
    st.markdown("---")
    
    # 录音区域
    audio_value = _render_recording_section()
    
    # 处理音频并显示结果
    if audio_value:
        _process_verification(audio_value, db, threshold)


def _render_config_section(db):
    """渲染配置区域"""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            st.metric(
                label="👥 注册用户数",
                value=len(db),
                help="当前系统中已注册的用户总数"
            )
        
        with col2:
            total_samples = sum(
                len(user_data.get("samples", [])) 
                if isinstance(user_data, dict) else 0 
                for user_data in db.values()
            )
            st.metric(
                label="🎵 声纹样本库",
                value=total_samples,
                help="所有用户的语音样本总数"
            )
        
        with col3:
            threshold = st.slider(
                "🎯 识别阈值",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_THRESHOLD,
                step=0.05,
                help="相似度阈值：值越高验证越严格，降低误识率但可能增加拒识率"
            )
    
    return threshold


def _render_recording_section():
    """渲染录音区域"""
    st.markdown("#### 🎙️ 语音录制")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        audio_value = st.audio_input(
            "点击麦克风按钮开始录制",
            label_visibility="collapsed",
            key=f"verify_audio_{st.session_state.verification_counter}"
        )
    
    with col_right:
        st.markdown("")
        st.markdown("")
        st.info("💡 **录音建议**\n\n清晰发音 · 2-5秒 · 安静环境")
    
    return audio_value


def _process_verification(audio_value, db, threshold):
    """处理验证流程"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_value.read())
        tmp_path = tmp_file.name
    
    try:
        st.markdown("---")
        st.markdown("#### 🔍 分析结果")
        
        # 读取音频
        audio_data, sr = sf.read(tmp_path)
        
        # 显示音频信息
        _display_audio_info(audio_value, audio_data, sr)
        
        # 提取特征并验证
        with st.spinner("🔍 正在进行声纹特征提取与匹配分析..."):
            probe_embedding = embed_audio(audio_data, sr)
            result = verify_voice(probe_embedding, db, threshold)
        
        st.markdown("")
        
        # 显示验证结果
        _display_verification_result(result)
        
        # 显示详细匹配结果
        _display_detailed_results(result)
        
        # 重新验证按钮
        _render_reset_button()
        
        os.unlink(tmp_path)
        
    except Exception as e:
        st.error(f"处理音频时出错: {e}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _display_audio_info(audio_value, audio_data, sr):
    """显示音频信息"""
    with st.container():
        col_play, col_info1, col_info2 = st.columns([3, 1, 1])
        with col_play:
            st.audio(audio_value)
        with col_info1:
            st.metric("⏱️ 时长", f"{len(audio_data)/sr:.1f}s")
        with col_info2:
            st.metric("📊 采样率", f"{sr}Hz")


def _display_verification_result(result):
    """显示验证结果"""
    matched_user = result["matched_user"]
    similarity = result["similarity"]
    threshold = result["threshold"]
    passed = result["passed"]
    
    if passed:
        # 验证通过
        st.markdown(SUCCESS_CARD_HTML, unsafe_allow_html=True)
        st.markdown("")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👤 识别用户", matched_user)
        with col2:
            st.metric("📊 匹配度", f"{similarity:.1%}", 
                     delta=f"+{(similarity-threshold)*100:.1f}%")
        with col3:
            st.metric("🎯 阈值", f"{threshold:.1%}")
    else:
        # 验证失败
        st.markdown(FAILURE_CARD_HTML, unsafe_allow_html=True)
        st.markdown("")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👤 最接近用户", matched_user)
        with col2:
            st.metric("📊 匹配度", f"{similarity:.1%}",
                     delta=f"{(similarity-threshold)*100:.1f}%",
                     delta_color="inverse")
        with col3:
            st.metric("🎯 阈值", f"{threshold:.1%}")


def _display_detailed_results(result):
    """显示详细匹配结果"""
    st.markdown("")
    
    with st.expander("📊 查看所有用户匹配详情", expanded=False):
        st.markdown("##### 匹配度排行")
        
        ranking = get_similarity_ranking(
            result["all_similarities"],
            result["threshold"]
        )
        
        for item in ranking:
            rank = item["rank"]
            user_id = item["user_id"]
            similarity = item["similarity"]
            passed = item["passed"]
            
            # 排名标识
            if rank == 1:
                rank_badge = "🥇"
            elif rank == 2:
                rank_badge = "🥈"
            elif rank == 3:
                rank_badge = "🥉"
            else:
                rank_badge = f"{rank}"
            
            # 状态标识
            status = "✅ 通过" if passed else "❌ 未通过"
            status_color = "#10b981" if passed else "#ef4444"
            
            col_a, col_b, col_c = st.columns([1, 3, 1])
            with col_a:
                st.markdown(f"<div style='font-size: 1.5rem;'>{rank_badge}</div>", 
                           unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**{user_id}**")
                st.progress(similarity, text=f"{similarity:.1%}")
            with col_c:
                st.markdown(f"<div style='color: {status_color}; font-weight: 600;'>{status}</div>",
                           unsafe_allow_html=True)


def _render_reset_button():
    """渲染重新验证按钮"""
    st.markdown("")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 进行新的验证", type="primary", 
                    use_container_width=True, key="new_verify_bottom"):
            st.session_state.verification_counter += 1
            st.rerun()
