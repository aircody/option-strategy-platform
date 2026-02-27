import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config

# Page configuration
st.set_page_config(
    page_title="期权策略分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'use_mock' not in st.session_state:
    st.session_state.use_mock = False
if 'api_error' not in st.session_state:
    st.session_state.api_error = None
if 'oi_subscription_data' not in st.session_state:
    st.session_state.oi_subscription_data = pd.DataFrame()

def init_longport_client():
    """Initialize LongPort client with credentials from environment"""
    try:
        from src.longport_client import LongportClient
        client = LongportClient()
        client.connect(
            app_key=Config.LONGPORT_APP_KEY,
            app_secret=Config.LONGPORT_APP_SECRET,
            access_token=Config.LONGPORT_ACCESS_TOKEN
        )
        st.session_state.client = client
        st.session_state.connected = True
        st.session_state.use_mock = False
        st.session_state.api_error = None
        return True
    except Exception as e:
        st.session_state.api_error = str(e)
        st.error(f"连接 LongPort API 失败: {str(e)}")
        return False

def init_mock_client():
    """Initialize mock client for demonstration"""
    from src.mock_data import generate_mock_option_chain, get_mock_expiry_dates, get_mock_stock_quote
    
    class MockClient:
        def get_expiry_dates(self, symbol):
            return get_mock_expiry_dates()
        
        def get_option_chain_by_date(self, symbol, expiry_date):
            return generate_mock_option_chain(symbol, expiry_date)
        
        def get_stock_quote(self, symbol):
            return get_mock_stock_quote(symbol)
    
    st.session_state.client = MockClient()
    st.session_state.connected = True
    st.session_state.use_mock = True
    st.session_state.api_error = None
    return True

def fetch_oi_data_for_symbols(symbols, expiry_date, delay=2):
    """Fetch OI data for multiple symbols with rate limiting"""
    from src.calculations import OICalculator
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    error_messages = []
    
    for i, symbol in enumerate(symbols):
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        
        status_text.text(f"正在获取 {symbol} 的数据... ({i+1}/{len(symbols)})")
        
        try:
            # Get stock quote
            stock_quote = st.session_state.client.get_stock_quote(symbol)
            spot_price = float(stock_quote.get('last_price', 0))
            
            # Add delay to avoid rate limiting
            if i > 0:
                time.sleep(delay)
            
            # Get option chain
            option_df = st.session_state.client.get_option_chain_by_date(symbol, expiry_date)
            
            if not option_df.empty:
                # Calculate weighted averages
                result = OICalculator.calculate_weighted_averages(option_df, spot_price)
                
                # Calculate Gap: (Spot - All WgtAvg) / All WgtAvg * 100
                if result.all_wgt_avg != 0:
                    gap = ((spot_price - result.all_wgt_avg) / result.all_wgt_avg) * 100
                else:
                    gap = 0
                
                results.append({
                    '股票代码': symbol,
                    '行权日': expiry_date,
                    'Spot': round(spot_price, 2),
                    'All WgtAvg': result.all_wgt_avg,
                    'Call WgtAvg': result.call_wgt_avg,
                    'Put WgtAvg': result.put_wgt_avg,
                    'Gap': round(gap, 2),
                    '状态': '成功'
                })
            else:
                results.append({
                    '股票代码': symbol,
                    '行权日': expiry_date,
                    'Spot': round(spot_price, 2),
                    'All WgtAvg': None,
                    'Call WgtAvg': None,
                    'Put WgtAvg': None,
                    'Gap': None,
                    '状态': '无期权数据'
                })
        except Exception as e:
            error_msg = str(e)
            if "Too many" in error_msg:
                error_messages.append(f"{symbol}: API请求过于频繁，请稍后再试")
                results.append({
                    '股票代码': symbol,
                    '行权日': expiry_date,
                    'Spot': None,
                    'All WgtAvg': None,
                    'Call WgtAvg': None,
                    'Put WgtAvg': None,
                    'Gap': None,
                    '状态': 'API限流'
                })
            else:
                error_messages.append(f"{symbol}: {error_msg}")
                results.append({
                    '股票代码': symbol,
                    '行权日': expiry_date,
                    'Spot': None,
                    'All WgtAvg': None,
                    'Call WgtAvg': None,
                    'Put WgtAvg': None,
                    'Gap': None,
                    '状态': '错误'
                })
        
        progress_bar.progress((i + 1) / len(symbols))
    
    progress_bar.empty()
    status_text.empty()
    
    # Show error messages if any
    if error_messages:
        with st.expander("⚠️ 部分股票获取失败"):
            for msg in error_messages:
                st.warning(msg)
    
    return pd.DataFrame(results)

# Sidebar
with st.sidebar:
    st.markdown("## 📊 期权策略分析平台")
    st.markdown("---")
    
    # API Connection Status
    if st.session_state.connected:
        if st.session_state.use_mock:
            st.info("ℹ️ 使用演示数据")
        else:
            st.success("✅ API 已连接")
            
            # Check if we have option permission
            if hasattr(st.session_state.client, 'has_option_permission') and not st.session_state.client.has_option_permission:
                st.error("⚠️ 无期权数据权限")
                st.markdown("""
                <div style="font-size: 12px; color: #666;">
                您的账号没有期权数据访问权限。<br>
                请前往 <a href="https://longportapp.com/" target="_blank">LongPort</a> 购买行情套餐。
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 未连接")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("连接 API", type="primary", use_container_width=True):
                with st.spinner("正在连接..."):
                    if init_longport_client():
                        st.success("连接成功！")
                        st.rerun()
        with col2:
            if st.button("演示模式", use_container_width=True):
                with st.spinner("加载演示数据..."):
                    if init_mock_client():
                        st.success("演示模式已启动！")
                        st.rerun()
    
    st.markdown("---")
    
    # Navigation
    st.markdown("## 导航")
    selected_tab = st.radio(
        "选择功能模块:",
        ["📈 期权链", "📈 OI走势图", "📈 策略分析", "⚙️ 设置"],
        index=0
    )

# Main content
st.markdown('<div class="main-header">期权策略分析平台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">基于 LongPort OpenAPI 的期权数据分析工具</div>', unsafe_allow_html=True)

# Option Chain Tab
if selected_tab == "📈 期权链":
    st.markdown("## 期权链分析")
    
    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
    else:
        # Check API permission status
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
        
        # Input section
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            symbol = st.text_input("股票代码", value="NVDA", placeholder="例如: NVDA, AAPL, TSLA").upper().strip()
        
        with col2:
            # Get expiry dates
            try:
                expiry_dates = st.session_state.client.get_expiry_dates(symbol)
                if expiry_dates:
                    selected_expiry = st.selectbox("到期日", expiry_dates)
                else:
                    if st.session_state.use_mock:
                        st.warning("未找到期权到期日")
                    else:
                        st.warning("未找到期权到期日 (可能需要购买期权行情权限)")
                    selected_expiry = None
            except Exception as e:
                st.error(f"获取到期日失败: {str(e)}")
                selected_expiry = None
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            fetch_button = st.button("获取数据", type="primary", use_container_width=True)
        
        # Fetch and display data
        if fetch_button and symbol and selected_expiry:
            with st.spinner("正在获取期权数据..."):
                try:
                    from src.calculations import OICalculator
                    from src.charts import create_oi_distribution_chart, create_metrics_cards
                    
                    # Get option chain
                    option_df = st.session_state.client.get_option_chain_by_date(symbol, selected_expiry)
                    
                    if option_df.empty:
                        st.warning("未找到期权数据")
                        
                        # Show more helpful message for API users
                        if not st.session_state.use_mock:
                            st.info("""
                            **可能的原因**:
                            1. API 账号没有期权数据权限（需要购买）
                            2. 该股票在当前到期日没有期权
                            3. 符号格式不正确（尝试 NVDA 或 NVDA.US）
                            
                            建议切换到「演示模式」查看功能效果。
                            """)
                    else:
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
                        with st.expander("查看原始数据"):
                            # Format the dataframe for display
                            # Convert Decimal types to float first
                            from src.calculations import OICalculator
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
                            
                            # Download button
                            csv = option_df.to_csv(index=False)
                            st.download_button(
                                label="下载 CSV",
                                data=csv,
                                file_name=f"{symbol}_options_{selected_expiry}.csv",
                                mime="text/csv"
                            )
                
                except Exception as e:
                    st.error(f"获取数据失败: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        # Batch query section
        st.markdown("---")
        st.markdown("## 期权链批量查询")
        st.markdown("批量获取多股票的期权加权平均数据")
        
        if not st.session_state.connected:
            st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
        else:
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
                # Use a default expiry date
                default_expiry = date.today().strftime("%Y-%m-%d")
                expiry_date = st.date_input(
                    "选择到期日",
                    value=datetime.strptime(default_expiry, "%Y-%m-%d"),
                    min_value=date.today()
                )
                expiry_date_str = expiry_date.strftime("%Y-%m-%d")
                
                # Add delay option
                st.markdown("<br>", unsafe_allow_html=True)
                delay = st.slider("请求间隔(秒)", min_value=1, max_value=5, value=2, 
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
                        df = fetch_oi_data_for_symbols(symbols, expiry_date_str, delay)
                        st.session_state.oi_subscription_data = df
            
            # Display results
            st.markdown("### 数据表格")
            
            if not st.session_state.oi_subscription_data.empty:
                # Format the dataframe for display
                display_df = st.session_state.oi_subscription_data.copy()
                
                # Use st.data_editor for sortable table
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
            
            # Tips section
            st.markdown("---")
            with st.expander("� 计算公式说明"):
                st.markdown("""
                ### 加权平均价计算公式
                
                **1. Call 期权加权平均行权价 (Call WgtAvg)**
                ```
                Call WgtAvg = Σ(Ki × CallOIi) / Σ(CallOIi)
                ```
                - Ki: 第 i 个行权价
                - CallOIi: 对应行权价的 Call 未平仓合约数
                
                **2. Put 期权加权平均行权价 (Put WgtAvg)**
                ```
                Put WgtAvg = Σ(Ki × PutOIi) / Σ(PutOIi)
                ```
                - Ki: 第 i 个行权价
                - PutOIi: 对应行权价的 Put 未平仓合约数
                
                **3. 整体 OI 重心 (All WgtAvg)**
                ```
                All WgtAvg = Σ(Ki × (CallOIi + PutOIi)) / Σ(CallOIi + PutOIi)
                ```
                
                **4. Gap 计算**
                ```
                Gap = (Spot - All WgtAvg) / All WgtAvg × 100%
                ```
                - Spot: 股票当前价格
                - All WgtAvg: 整体加权平均行权价
                - **正值**: 现货价格高于 OI 重心，可能看涨
                - **负值**: 现货价格低于 OI 重心，可能看跌
                """)

# OI Trend Chart Tab
elif selected_tab == "📈 OI走势图":
    st.markdown("## OI 走势图")
    st.markdown("查看不同到期日的加权平均价趋势")
    
    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
    else:
        # Input section
        col1, col2 = st.columns([1, 3])
        
        with col1:
            symbol = st.text_input("股票代码", value="NVDA", placeholder="例如: NVDA, AAPL, TSLA").upper().strip()
        
        with col2:
            # Get expiry dates
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
                else:
                    st.warning("未找到期权到期日")
                    selected_dates = []
            except Exception as e:
                st.error(f"获取到期日失败: {str(e)}")
                selected_dates = []
        
        # Request delay setting with enhanced UI
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
        
        # Fetch and display trend data
        if symbol and selected_dates and len(selected_dates) > 0:
            if st.button("生成走势图", type="primary"):
                with st.spinner("正在获取数据..."):
                    try:
                        from src.calculations import OICalculator
                        from src.charts import create_oi_trend_chart
                        
                        # Sort dates chronologically
                        selected_dates_sorted = sorted(selected_dates)
                        
                        # Fetch data for each expiry date
                        trend_data = []
                        progress_bar = st.progress(0)
                        
                        for i, expiry_date in enumerate(selected_dates_sorted):
                            try:
                                # Get stock quote
                                stock_quote = st.session_state.client.get_stock_quote(symbol)
                                spot_price = float(stock_quote.get('last_price', 0))
                                
                                # Add delay to avoid API rate limiting
                                if i > 0:
                                    time.sleep(request_delay)  # Custom delay between requests
                                
                                # Get option chain
                                option_df = st.session_state.client.get_option_chain_by_date(symbol, expiry_date)
                                
                                if not option_df.empty:
                                    # Calculate weighted averages
                                    result = OICalculator.calculate_weighted_averages(option_df, spot_price)
                                    
                                    trend_data.append({
                                        'expiry_date': expiry_date,
                                        'call_wgt_avg': result.call_wgt_avg,
                                        'put_wgt_avg': result.put_wgt_avg,
                                        'all_wgt_avg': result.all_wgt_avg,
                                        'spot_price': spot_price
                                    })
                                else:
                                    st.warning(f"{expiry_date}: 无期權数据")
                            except Exception as e:
                                error_msg = str(e)
                                if "Too many" in error_msg:
                                    st.warning(f"{expiry_date}: API请求过于频繁，请稍后再试")
                                else:
                                    st.warning(f"{expiry_date}: 获取数据失败 - {error_msg}")
                            
                            progress_bar.progress((i + 1) / len(selected_dates_sorted))
                        
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
                        else:
                            st.warning("没有获取到有效的期权数据")
                    
                    except Exception as e:
                        st.error(f"生成走势图失败: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())

# Strategy Analysis Tab
elif selected_tab == "📈 策略分析":
    st.markdown("## 策略分析")
    
    if not st.session_state.connected:
        st.info("👈 请先点击左侧的「连接 API」或「演示模式」按钮")
    else:
        st.info("策略分析功能开发中...")
        
        # Placeholder for future strategy analysis features
        st.markdown("### 计划功能")
        st.markdown("- 跨期套利分析")
        st.markdown("- 波动率曲面")
        st.markdown("- 希腊字母分析")
        st.markdown("- 策略回测")

# Settings Tab
elif selected_tab == "⚙️ 设置":
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

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 12px;'>"
    "© 2026 期权策略分析平台 | Powered by LongPort OpenAPI"
    "</div>",
    unsafe_allow_html=True
)
