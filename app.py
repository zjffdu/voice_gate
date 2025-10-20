"""Voice Gate - 主应用入口"""

import streamlit as st
from voice_gate.config import ENROLLMENT_SAMPLES_COUNT
from voice_gate.database import load_db, get_user_stats
from voice_gate.audio_processor import get_encoder
from voice_gate.ui.sidebar import render_sidebar
from voice_gate.ui.enrollment_page import render_enrollment_page
from voice_gate.ui.verification_page import render_verification_page
from voice_gate.ui.database_page import render_database_page
from voice_gate.ui_styles import CUSTOM_CSS, MAIN_HEADER_HTML, SUB_HEADER_HTML


def init_session_state():
    """初始化所有session state（避免tab切换时的状态初始化导致页面跳转）"""
    if "verification_counter" not in st.session_state:
        st.session_state.verification_counter = 0
    
    if "enrollment_samples" not in st.session_state:
        st.session_state.enrollment_samples = []
    
    if "enrollment_audio_files" not in st.session_state:
        st.session_state.enrollment_audio_files = []
    
    if "enrollment_audio_hashes" not in st.session_state:
        st.session_state.enrollment_audio_hashes = [None] * ENROLLMENT_SAMPLES_COUNT


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title="Voice Gate - 声纹识别系统",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 应用自定义样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 主标题
    st.markdown(MAIN_HEADER_HTML, unsafe_allow_html=True)
    st.markdown(SUB_HEADER_HTML, unsafe_allow_html=True)
    
    # 预加载模型
    with st.spinner("正在初始化语音识别引擎..."):
        get_encoder()
    
    # 加载数据库
    db = load_db()
    
    # 初始化session state
    init_session_state()
    
    # 渲染侧边栏
    db_stats = get_user_stats(db)
    render_sidebar(db_stats)
    
    # 创建tabs
    tab1, tab2, tab3 = st.tabs(["👤 注册用户", "🔐 验证身份", "📊 数据库管理"])
    
    with tab1:
        render_enrollment_page(db)
    
    with tab2:
        render_verification_page(db)
    
    with tab3:
        render_database_page(db)


if __name__ == "__main__":
    main()
