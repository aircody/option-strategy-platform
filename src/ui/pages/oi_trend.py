import streamlit as st
import pandas as pd

from src.services.data_fetcher import DataFetcher
from src.charts import create_oi_trend_chart


def render_oi_trend_page():
    """Render OI trend chart page"""
    st.markdown("## OI 走势图")
    st.markdown("查看不同到期日的加权平均价趋势")

    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
        return

    # Input section
    symbol, selected_dates = _render_input_section()

    # Request delay setting
    request_delay = _render_delay_settings(selected_dates)

    # Fetch and display trend data
    if symbol and selected_dates and len(selected_dates) > 0:
        if st.button("生成走势图", type="primary"):
            _fetch_and_display_trend_data(symbol, selected_dates, request_delay)


def _render_input_section():
    """Render input section for symbol and expiry dates"""
    col1, col2 = st.columns([1, 3])

    with col1:
        symbol = st.text_input("股票代码", value="NVDA", placeholder="例如: NVDA, AAPL, TSLA").upper().strip()

    with col2:
        selected_dates = _render_expiry_date_selector(symbol)

    return symbol, selected_dates


def _render_expiry_date_selector(symbol: str):
    """Render expiry date selector"""
    try:
        expiry_dates = st.session_state.client.get_expiry_dates(symbol)
        if expiry_dates and len(expiry_dates) > 0:
            # Allow user to select date range
            selected_dates = st.multiselect(
                "选择到期日区间（可多选）",
                options=expiry_dates,
                default=expiry_dates[:5] if len(expiry_dates) >= 5 else expiry_dates,
                help="选择要查看的到期日，将按时间顺序显示趋势"
            )
            return selected_dates
        else:
            st.warning("未找到期权到期日")
            return []
    except Exception as e:
        st.error(f"获取到期日失败: {str(e)}")
        return []


def _render_delay_settings(selected_dates):
    """Render request delay settings"""
    st.markdown("### ⏱️ 请求设置")

    delay_col1, delay_col2, delay_col3 = st.columns([2, 2, 3])

    with delay_col1:
        # Quick preset buttons
        st.markdown("**快速设置**")
        preset_col1, preset_col2, preset_col3 = st.columns(3)
        with preset_col1:
            if st.button("🚀 快速", help="1秒间隔，适合少量数据", use_container_width=True):
                st.session_state.request_delay = 1
        with preset_col2:
            if st.button("⚖️ 平衡", help="3秒间隔，推荐设置", use_container_width=True):
                st.session_state.request_delay = 3
        with preset_col3:
            if st.button("🐢 稳定", help="5秒间隔，避免限流", use_container_width=True):
                st.session_state.request_delay = 5

    with delay_col2:
        # Number input for precise control
        st.markdown("**精确设置**")
        request_delay = st.number_input(
            "间隔(秒)",
            min_value=1,
            max_value=60,
            value=st.session_state.get('request_delay', 2),
            step=1,
            help="自定义请求间隔，范围1-60秒"
        )
        # Update session state
        st.session_state.request_delay = request_delay

    with delay_col3:
        # Visual indicator and tips
        st.markdown("**状态提示**")
        if request_delay <= 2:
            st.info(f"⏱️ 当前间隔: **{request_delay}秒** - 速度优先，适合1-3个到期日")
        elif request_delay <= 5:
            st.success(f"⏱️ 当前间隔: **{request_delay}秒** - 推荐设置，适合3-6个到期日")
        elif request_delay <= 10:
            st.warning(f"⏱️ 当前间隔: **{request_delay}秒** - 保守设置，适合6-10个到期日")
        else:
            st.error(f"⏱️ 当前间隔: **{request_delay}秒** - 超保守设置，仅适合大量数据或网络不稳定时")

        # Estimated time
        if selected_dates:
            est_time = len(selected_dates) * (request_delay + 1)  # +1 for processing time
            st.caption(f"预计耗时: 约 {est_time} 秒")

    return request_delay


def _fetch_and_display_trend_data(symbol: str, selected_dates: list, request_delay: int):
    """Fetch and display trend data"""
    with st.spinner("正在获取数据..."):
        try:
            fetcher = DataFetcher(st.session_state.client)

            # Sort dates chronologically
            selected_dates_sorted = sorted(selected_dates)

            # Fetch data for each expiry date
            progress_bar = st.progress(0)

            def progress_callback(current, total):
                progress = min(current / total, 1.0) if total > 0 else 0.0
                progress_bar.progress(progress)

            trend_data = fetcher.fetch_trend_data(
                symbol,
                selected_dates_sorted,
                request_delay,
                progress_callback
            )

            progress_bar.empty()

            # Display trend chart
            if trend_data:
                trend_df = pd.DataFrame(trend_data)

                # Get latest spot price
                latest_spot = trend_df['spot_price'].iloc[-1] if not trend_df.empty else 0

                # Create and display chart
                fig = create_oi_trend_chart(trend_df, symbol, latest_spot)
                st.plotly_chart(fig, use_container_width=True)

                # Display data table
                _render_data_table(trend_df, symbol)
            else:
                st.warning("没有获取到有效的期权数据")

        except Exception as e:
            st.error(f"生成走势图失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def _render_data_table(trend_df: pd.DataFrame, symbol: str):
    """Render data table with download option"""
    with st.expander("查看数据"):
        display_df = trend_df.copy()
        display_df['call_wgt_avg'] = display_df['call_wgt_avg'].round(2)
        display_df['put_wgt_avg'] = display_df['put_wgt_avg'].round(2)
        display_df['all_wgt_avg'] = display_df['all_wgt_avg'].round(2)
        display_df['spot_price'] = display_df['spot_price'].round(2)

        st.dataframe(
            display_df,
            column_config={
                'expiry_date': '到期日',
                'call_wgt_avg': 'Call WgtAvg',
                'put_wgt_avg': 'Put WgtAvg',
                'all_wgt_avg': 'All WgtAvg',
                'spot_price': 'Spot Price'
            },
            hide_index=True
        )

        # Download button
        csv = trend_df.to_csv(index=False)
        st.download_button(
            label="下载 CSV",
            data=csv,
            file_name=f"{symbol}_oi_trend.csv",
            mime="text/csv"
        )
