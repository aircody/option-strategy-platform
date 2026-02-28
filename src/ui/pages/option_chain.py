import streamlit as st
import pandas as pd
from datetime import datetime, date

from src.services.data_fetcher import DataFetcher
from src.calculations import OICalculator
from src.charts import create_oi_distribution_chart, create_metrics_cards


def render_option_chain_page():
    """Render option chain analysis page"""
    st.markdown("## 期权链分析")

    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
        return

    # Check API permission status
    _check_permission()

    # Input section
    symbol, selected_expiry, fetch_button = _render_input_section()

    # Fetch and display data
    if fetch_button and symbol and selected_expiry:
        _fetch_and_display_data(symbol, selected_expiry)

    # Batch query section
    _render_batch_query_section()


def _check_permission():
    """Check and display API permission status"""
    if not st.session_state.use_mock:
        if hasattr(st.session_state.client, 'has_option_permission') and not st.session_state.client.has_option_permission:
            st.error("⚠️ API 账号无期权数据权限")
            st.info("""
            **原因**: 您的 LongPort API 账号没有购买期权行情数据权限。

            **解决方案**:
            1. 前往 [LongPort 官网](https://longportapp.com/) 购买期权行情套餐
            2. 或使用左侧的「演示模式」查看功能效果

            **错误详情**: 
            ```
            USOption | You do not have access to the market's Open API data. 
            Please visit the Quotes Store to purchase.
            ```
            """)


def _render_input_section():
    """Render input section for symbol and expiry date"""
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        symbol = st.text_input("股票代码", value="NVDA", placeholder="例如: NVDA, AAPL, TSLA").upper().strip()

    with col2:
        selected_expiry = _render_expiry_date_selector(symbol)

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_button = st.button("获取数据", type="primary", use_container_width=True)

    return symbol, selected_expiry, fetch_button


def _render_expiry_date_selector(symbol: str):
    """Render expiry date selector"""
    try:
        expiry_dates = st.session_state.client.get_expiry_dates(symbol)
        if expiry_dates:
            return st.selectbox("到期日", expiry_dates)
        else:
            if st.session_state.use_mock:
                st.warning("未找到期权到期日")
            else:
                st.warning("未找到期权到期日 (可能需要购买期权行情权限)")
            return None
    except Exception as e:
        st.error(f"获取到期日失败: {str(e)}")
        return None


def _fetch_and_display_data(symbol: str, selected_expiry: str):
    """Fetch and display option chain data"""
    with st.spinner("正在获取期权数据..."):
        try:
            # Get option chain
            option_df = st.session_state.client.get_option_chain_by_date(symbol, selected_expiry)

            if option_df.empty:
                st.warning("未找到期权数据")
                _show_no_data_help()
                return

            # Get stock quote for spot price
            stock_quote = st.session_state.client.get_stock_quote(symbol)
            spot_price = stock_quote.get('last_price', 0)

            # Calculate weighted averages
            result = OICalculator.calculate_weighted_averages(option_df, spot_price)

            # Prepare chart data
            chart_df = OICalculator.prepare_oi_distribution_data(option_df)

            # Display metrics
            st.markdown("### 关键指标")
            st.markdown(create_metrics_cards(result, symbol), unsafe_allow_html=True)

            # Display chart
            st.markdown("### OI 分布图")
            fig = create_oi_distribution_chart(
                chart_df,
                result,
                symbol,
                selected_expiry,
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display data table
            _render_data_table(option_df, symbol, selected_expiry)

        except Exception as e:
            st.error(f"获取数据失败: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def _show_no_data_help():
    """Show help message when no data is available"""
    if not st.session_state.use_mock:
        st.info("""
        **可能的原因**:
        1. API 账号没有期权数据权限（需要购买）
        2. 该股票在当前到期日没有期权
        3. 符号格式不正确（尝试 NVDA 或 NVDA.US）

        建议切换到「演示模式」查看功能效果。
        """)


def _render_data_table(option_df: pd.DataFrame, symbol: str, selected_expiry: str):
    """Render data table with download option"""
    with st.expander("查看原始数据"):
        display_df = OICalculator._convert_dataframe_types(option_df.copy())

        display_df['last_price'] = display_df['last_price'].round(2)
        display_df['bid'] = display_df['bid'].round(2)
        display_df['ask'] = display_df['ask'].round(2)
        display_df['implied_volatility'] = (display_df['implied_volatility'] * 100).round(2)
        display_df['delta'] = display_df['delta'].round(4)
        display_df['gamma'] = display_df['gamma'].round(4)
        display_df['theta'] = display_df['theta'].round(4)
        display_df['vega'] = display_df['vega'].round(4)

        st.dataframe(
            display_df,
            column_config={
                'symbol': '期权代码',
                'strike': '行权价',
                'option_type': '类型',
                'open_interest': '持仓量',
                'volume': '成交量',
                'last_price': '最新价',
                'bid': '买价',
                'ask': '卖价',
                'implied_volatility': '隐含波动率(%)',
                'delta': 'Delta',
                'gamma': 'Gamma',
                'theta': 'Theta',
                'vega': 'Vega'
            },
            hide_index=True
        )

        csv = option_df.to_csv(index=False)
        st.download_button(
            label="下载 CSV",
            data=csv,
            file_name=f"{symbol}_options_{selected_expiry}.csv",
            mime="text/csv"
        )


def _render_batch_query_section():
    """Render batch query section"""
    st.markdown("---")
    st.markdown("## 期权链批量查询")
    st.markdown("批量获取多股票的期权加权平均数据")

    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
        return

    # Input section
    st.markdown("### 添加股票")

    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        symbols_input = st.text_area(
            "股票代码（每行一个）",
            value="NVDA\nAAPL\nTSLA\nAMD\nMSFT",
            placeholder="例如:\nNVDA\nAAPL\nTSLA",
            height=150
        )

    with col2:
        default_expiry = date.today().strftime("%Y-%m-%d")
        expiry_date = st.date_input(
            "选择到期日",
            value=datetime.strptime(default_expiry, "%Y-%m-%d"),
            min_value=date.today()
        )
        expiry_date_str = expiry_date.strftime("%Y-%m-%d")

        st.markdown("<br>", unsafe_allow_html=True)
        delay = st.slider("请求间隔(秒)", min_value=1, max_value=60, value=2,
                        help="为避免API限流，设置每个股票之间的请求间隔")

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_all_button = st.button("批量获取数据", type="primary", use_container_width=True)
        clear_button = st.button("清空数据", use_container_width=True)

    # Clear data
    if clear_button:
        st.session_state.oi_subscription_data = pd.DataFrame()
        st.rerun()

    # Fetch data for all symbols
    if fetch_all_button:
        symbols = [s.strip() for s in symbols_input.split('\n') if s.strip()]

        if not symbols:
            st.warning("请输入至少一个股票代码")
        else:
            with st.spinner("正在批量获取数据..."):
                fetcher = DataFetcher(st.session_state.client)
                progress_bar = st.progress(0)

                def progress_callback(current, total):
                    progress_bar.progress(current / total)

                df = fetcher.fetch_oi_data_for_symbols(
                    symbols,
                    expiry_date_str,
                    delay,
                    progress_callback
                )
                st.session_state.oi_subscription_data = df

    # Display results
    _render_batch_results(expiry_date_str)


def _render_batch_results(expiry_date_str: str):
    """Render batch query results"""
    st.markdown("### 数据表格")

    if not st.session_state.oi_subscription_data.empty:
        display_df = st.session_state.oi_subscription_data.copy()

        st.dataframe(
            display_df,
            column_config={
                '股票代码': st.column_config.TextColumn('股票代码'),
                '行权日': st.column_config.TextColumn('行权日'),
                'Spot': st.column_config.NumberColumn('Spot', format="%.2f"),
                'All WgtAvg': st.column_config.NumberColumn('All WgtAvg', format="%.2f"),
                'Call WgtAvg': st.column_config.NumberColumn('Call WgtAvg', format="%.2f"),
                'Put WgtAvg': st.column_config.NumberColumn('Put WgtAvg', format="%.2f"),
                'Gap': st.column_config.NumberColumn('Gap (%)', format="%.2f%%"),
                '状态': st.column_config.TextColumn('状态')
            },
            hide_index=True
        )

        # Summary statistics
        _render_summary_statistics(display_df)

        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="下载 CSV",
            data=csv,
            file_name=f"oi_subscription_{expiry_date_str}.csv",
            mime="text/csv"
        )
    else:
        st.info("点击「批量获取数据」按钮开始获取股票数据")


def _render_summary_statistics(display_df: pd.DataFrame):
    """Render summary statistics"""
    st.markdown("### 统计摘要")
    col1, col2, col3, col4 = st.columns(4)

    valid_data = display_df[display_df['Gap'].notna()]

    with col1:
        st.metric("股票数量", len(display_df))
    with col2:
        st.metric("成功获取", len(valid_data))
    with col3:
        failed_count = len(display_df[display_df['状态'] != '成功'])
        st.metric("失败/无数据", failed_count)
    with col4:
        if not valid_data.empty:
            avg_gap = valid_data['Gap'].mean()
            st.metric("平均 Gap", f"{avg_gap:.2f}%")
        else:
            st.metric("平均 Gap", "N/A")
