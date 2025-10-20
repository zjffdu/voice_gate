"""侧边栏组件"""

import streamlit as st
from voice_gate.ui_styles import USAGE_GUIDE


def render_sidebar(db_stats):
    """
    渲染侧边栏
    
    Args:
        db_stats: 数据库统计信息字典
    """
    with st.sidebar:
        st.markdown("### 📊 系统概览")
        st.markdown("")
        
        # 统计卡片
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="👥 用户数",
                value=db_stats["total_users"],
                delta=None
            )
        with col2:
            st.metric(
                label="🎵 样本数",
                value=db_stats["total_samples"],
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
            st.markdown(USAGE_GUIDE)
        
        st.markdown("---")
        st.caption("Powered by Resemblyzer · v1.0.0")
