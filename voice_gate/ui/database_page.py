"""数据库管理页面"""

import os
import tempfile
import hashlib
import streamlit as st
import soundfile as sf
from datetime import datetime
from voice_gate.audio_processor import embed_audio, save_audio_sample, calculate_prototype
from voice_gate.database import delete_user, delete_user_sample, save_db
from voice_gate.ui_styles import EMPTY_DB_HTML, get_gradient_card_html, get_info_box_html


def render_database_page(db):
    """
    渲染数据库管理页面
    
    Args:
        db: 数据库字典
    """
    st.markdown("### 📊 数据库管理")
    st.markdown("管理用户声纹数据，支持查看、编辑和删除操作")
    st.markdown("")
    
    if not db:
        st.markdown(EMPTY_DB_HTML, unsafe_allow_html=True)
        return
    
    # 统计仪表板
    _render_stats_dashboard(db)
    
    st.markdown("")
    st.markdown("---")
    st.markdown("#### 👥 用户列表")
    
    # 遍历每个用户
    for user_id in list(db.keys()):
        _render_user_detail(user_id, db)


def _render_stats_dashboard(db):
    """渲染统计仪表板"""
    st.markdown("#### 📈 数据统计")
    
    total_samples = sum(
        len(user_data.get("samples", [])) 
        if isinstance(user_data, dict) else 0 
        for user_data in db.values()
    )
    avg_samples = total_samples / len(db) if len(db) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            get_gradient_card_html(
                "👥", len(db), "注册用户",
                "#667eea 0%, #764ba2 100%"
            ),
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            get_gradient_card_html(
                "🎵", total_samples, "语音样本",
                "#f093fb 0%, #f5576c 100%"
            ),
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            get_gradient_card_html(
                "📊", f"{avg_samples:.1f}", "平均样本",
                "#4facfe 0%, #00f2fe 100%"
            ),
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            get_gradient_card_html(
                "💾", "256", "特征维度",
                "#43e97b 0%, #38f9d7 100%"
            ),
            unsafe_allow_html=True
        )


def _render_user_detail(user_id, db):
    """渲染用户详情"""
    user_data = db[user_id]
    
    with st.expander(f"👤 {user_id}", expanded=False):
        if isinstance(user_data, dict):
            _render_user_info(user_id, user_data, db)
            st.markdown("")
            _render_user_samples(user_id, user_data, db)
            _render_add_sample_section(user_id, user_data, db)
        else:
            st.info("ℹ️ 旧版本数据（仅包含声纹特征）")


def _render_user_info(user_id, user_data, db):
    """渲染用户信息"""
    created_time = user_data.get('created_at', '未知')
    if created_time != '未知':
        try:
            dt = datetime.fromisoformat(created_time)
            created_time = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    col_info1, col_info2, col_action = st.columns([2, 2, 1])
    
    with col_info1:
        st.markdown(
            get_info_box_html("📅 注册时间", created_time),
            unsafe_allow_html=True
        )
    
    with col_info2:
        sample_count = len(user_data.get('samples', []))
        st.markdown(
            get_info_box_html("🎵 语音样本", f"{sample_count} 个"),
            unsafe_allow_html=True
        )
    
    with col_action:
        st.markdown("")
        if st.button("🗑️ 删除用户", key=f"del_{user_id}", 
                    type="secondary", use_container_width=True):
            if delete_user(db, user_id):
                st.success(f"✅ 已删除用户 {user_id}")
                st.rerun()


def _render_user_samples(user_id, user_data, db):
    """渲染用户样本"""
    if "samples" not in user_data:
        return
    
    if user_data["samples"]:
        st.markdown("##### 🎵 语音样本库")
        st.markdown("")
        
        cols_per_row = 3
        for i in range(0, len(user_data["samples"]), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx_sample = i + j
                if idx_sample < len(user_data["samples"]):
                    audio_path = user_data["samples"][idx_sample]
                    with col:
                        _render_sample_card(user_id, idx_sample, audio_path, db)
        
        st.markdown("")
    else:
        st.info("ℹ️ 该用户暂无录音样本")


def _render_sample_card(user_id, idx_sample, audio_path, db):
    """渲染单个样本卡片"""
    with st.container(border=True):
        if os.path.exists(audio_path):
            st.markdown(f"**样本 {idx_sample + 1}**")
            st.audio(audio_path)
            st.caption(f"`{os.path.basename(audio_path)}`")
            
            if st.button("🗑️ 删除", key=f"del_audio_{user_id}_{idx_sample}",
                        use_container_width=True):
                if delete_user_sample(db, user_id, audio_path):
                    st.success(f"✅ 已删除样本 {idx_sample + 1}")
                    st.rerun()
        else:
            st.warning(f"⚠️ 文件不存在")
            st.caption(f"`{os.path.basename(audio_path)}`")


def _render_add_sample_section(user_id, user_data, db):
    """渲染添加样本区域"""
    st.markdown("---")
    st.markdown("##### ➕ 添加新样本")
    st.markdown("录制新的语音样本以增强识别准确率")
    
    col_audio, col_tip = st.columns([3, 1])
    
    with col_audio:
        new_audio = st.audio_input(
            f"录制新样本",
            key=f"add_audio_{user_id}",
            label_visibility="collapsed"
        )
    
    with col_tip:
        st.markdown("")
        st.markdown("")
        st.info("💡 建议录制 2-5 秒")
    
    if new_audio:
        _process_new_sample(new_audio, user_id, user_data, db)


def _process_new_sample(new_audio, user_id, user_data, db):
    """处理新样本"""
    # 使用session state跟踪已处理的音频
    audio_session_key = f"processed_audio_{user_id}"
    if audio_session_key not in st.session_state:
        st.session_state[audio_session_key] = None
    
    # 获取音频哈希值
    audio_bytes = new_audio.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    # 只处理新音频
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
                
                # 重新计算原型向量
                all_embeddings = [new_embedding]
                for sample_path in user_data["samples"]:
                    if os.path.exists(sample_path):
                        sample_audio, sample_sr = sf.read(sample_path)
                        all_embeddings.append(embed_audio(sample_audio, sample_sr))
                
                user_data["embedding"] = calculate_prototype(all_embeddings)
                user_data["samples"].append(saved_path)
                save_db(db)
                
                # 标记已处理
                st.session_state[audio_session_key] = audio_hash
            
            os.unlink(tmp_path)
            st.success(f"✅ 新样本已添加，声纹特征已更新")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 处理音频时出错: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        st.info("ℹ️ 此音频样本已添加，请录制新的音频")
