"""UI样式定义"""

# 页面标题样式
MAIN_HEADER_HTML = '<h1 class="main-header">🎙️ Voice Gate</h1>'
SUB_HEADER_HTML = '<p class="sub-header">企业级声纹识别与身份验证平台</p>'

# CSS样式
CUSTOM_CSS = """
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
"""

# 验证通过卡片
SUCCESS_CARD_HTML = """
<div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
            padding: 2rem; border-radius: 12px; border-left: 5px solid #10b981;'>
    <h2 style='color: #065f46; margin: 0;'>✅ 验证通过</h2>
    <p style='color: #047857; font-size: 1.2rem; margin-top: 0.5rem;'>
        身份确认成功，欢迎回来！
    </p>
</div>
"""

# 验证失败卡片
FAILURE_CARD_HTML = """
<div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
            padding: 2rem; border-radius: 12px; border-left: 5px solid #ef4444;'>
    <h2 style='color: #991b1b; margin: 0;'>❌ 验证失败</h2>
    <p style='color: #dc2626; font-size: 1.2rem; margin-top: 0.5rem;'>
        声纹匹配度不足，身份验证未通过
    </p>
</div>
"""

# 空数据库展示
EMPTY_DB_HTML = """
<div style='text-align: center; padding: 4rem 2rem; background: #f8fafc; border-radius: 12px;'>
    <div style='font-size: 4rem; margin-bottom: 1rem;'>📭</div>
    <h3 style='color: #64748b;'>数据库为空</h3>
    <p style='color: #94a3b8;'>暂无注册用户，请前往「用户注册」页面添加用户</p>
</div>
"""

# 使用指南内容
USAGE_GUIDE = """
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
"""


def get_metric_card_html(icon, value, label):
    """生成指标卡片HTML"""
    return f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 12px; color: white;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
        <div style='font-size: 2rem; font-weight: 700;'>{value}</div>
        <div style='opacity: 0.9;'>{label}</div>
    </div>
    """


def get_gradient_card_html(icon, value, label, gradient):
    """生成渐变卡片HTML"""
    return f"""
    <div style='background: linear-gradient(135deg, {gradient}); 
                padding: 1.5rem; border-radius: 12px; color: white;'>
        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
        <div style='font-size: 2rem; font-weight: 700;'>{value}</div>
        <div style='opacity: 0.9;'>{label}</div>
    </div>
    """


def get_info_box_html(title, content, color="#64748b"):
    """生成信息框HTML"""
    return f"""
    <div style='background: #f8fafc; padding: 1rem; border-radius: 8px;'>
        <div style='color: {color}; font-size: 0.875rem;'>{title}</div>
        <div style='color: #1e293b; font-weight: 600; margin-top: 0.25rem;'>{content}</div>
    </div>
    """
