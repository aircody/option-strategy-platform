import streamlit as st

from src.services.client_factory import ClientFactory


def render_sidebar():
    """Render sidebar with navigation and connection status"""
    st.markdown("## 📊 期权策略分析平台")
    st.markdown("---")

    # API Connection Status
    _render_connection_status()

    st.markdown("---")

    # Navigation
    st.markdown("## 导航")
    selected_tab = st.radio(
        "选择功能模块:",
        ["📈 期权链", "📈 OI走势图", "📈 策略分析", "⚙️ 设置"],
        index=0
    )

    return selected_tab


def _render_connection_status():
    """Render API connection status and controls"""
    if st.session_state.connected:
        if st.session_state.use_mock:
            st.info("ℹ️ 使用演示数据")
        else:
            st.success("✅ API 已连接")
            _check_option_permission()
    else:
        st.warning("⚠️ 未连接")
        _render_connection_buttons()


def _check_option_permission():
    """Check and display option permission status"""
    if hasattr(st.session_state.client, 'has_option_permission') and not st.session_state.client.has_option_permission:
        st.error("⚠️ 无期权数据权限")
        st.markdown("""
        <div style="font-size: 12px; color: #666;">
        您的账号没有期权数据访问权限。<br>
        请前往 <a href="https://longportapp.com/" target="_blank">LongPort</a> 购买行情套餐。
        </div>
        """, unsafe_allow_html=True)


def _render_connection_buttons():
    """Render connection buttons"""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("连接 API", type="primary", use_container_width=True):
            with st.spinner("正在连接..."):
                client = ClientFactory.create_longport_client()
                if client:
                    st.session_state.client = client
                    st.session_state.connected = True
                    st.session_state.use_mock = False
                    st.session_state.api_error = None
                    st.success("连接成功！")
                    st.rerun()
    with col2:
        if st.button("演示模式", use_container_width=True):
            with st.spinner("加载演示数据..."):
                client = ClientFactory.create_mock_client()
                st.session_state.client = client
                st.session_state.connected = True
                st.session_state.use_mock = True
                st.session_state.api_error = None
                st.success("演示模式已启动！")
                st.rerun()
