import streamlit as st

from src.utils.session_state import init_session_state
from src.utils.styles import get_custom_css, get_footer
from src.ui.sidebar import render_sidebar
from src.ui.pages.option_chain import render_option_chain_page
from src.ui.pages.oi_trend import render_oi_trend_page
from src.ui.pages.strategy_analysis import render_strategy_analysis_page
from src.ui.pages.settings import render_settings_page


# Page configuration
st.set_page_config(
    page_title="期权策略分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Render sidebar
selected_tab = render_sidebar()

# Main content
st.markdown('<div class="main-header">期权策略分析平台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">基于 LongPort OpenAPI 的期权数据分析工具</div>', unsafe_allow_html=True)

# Route to selected page
if selected_tab == "📈 期权链":
    render_option_chain_page()
elif selected_tab == "📈 OI走势图":
    render_oi_trend_page()
elif selected_tab == "📈 策略分析":
    render_strategy_analysis_page()
elif selected_tab == "⚙️ 设置":
    render_settings_page()

# Footer
st.markdown("---")
st.markdown(get_footer(), unsafe_allow_html=True)
