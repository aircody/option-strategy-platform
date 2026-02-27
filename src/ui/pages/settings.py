import streamlit as st

from src.config import Config


def render_settings_page():
    """Render settings page"""
    st.markdown("## 设置")

    st.markdown("### API 配置")
    st.markdown(f"- **App Key**: {'*' * 10}{Config.LONGPORT_APP_KEY[-4:] if Config.LONGPORT_APP_KEY else '未设置'}")
    st.markdown(f"- **App Secret**: {'*' * 20}{Config.LONGPORT_APP_SECRET[-4:] if Config.LONGPORT_APP_SECRET else '未设置'}")
    st.markdown(f"- **Access Token**: {'*' * 30}...")

    st.markdown("---")

    # Connection Status
    st.markdown("### 连接状态")
    if st.session_state.connected:
        if st.session_state.use_mock:
            st.info("当前模式: 演示模式")
        else:
            st.success("当前模式: API 连接")
            if hasattr(st.session_state.client, 'has_option_permission'):
                if st.session_state.client.has_option_permission:
                    st.success("期权数据权限: ✅ 有权限")
                else:
                    st.error("期权数据权限: ❌ 无权限")
                    st.markdown("""
                    **权限详情**:
                    ```
                    USOption | You do not have access to the market's Open API data. 
                    Please visit the Quotes Store to purchase.
                    ```
                    """)
    else:
        st.warning("当前状态: 未连接")

    st.markdown("---")

    st.markdown("### 关于")
    st.markdown("- **版本**: 1.0.0")
    st.markdown("- **数据来源**: LongPort OpenAPI")
    st.markdown("- **技术支持**: [LongPort 开发者文档](https://open.longportapp.com/)")
