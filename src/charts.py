import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional
from src.calculations import WeightedAverageResult

def create_oi_distribution_chart(
    df: pd.DataFrame,
    result: WeightedAverageResult,
    symbol: str,
    expiry_date: str,
    height: int = 500
) -> go.Figure:
    """
    Create OI distribution chart similar to the reference image
    
    Args:
        df: DataFrame with OI distribution data (strike, call_oi, put_oi)
        result: WeightedAverageResult with calculated values
        symbol: Stock symbol
        expiry_date: Expiry date string
        height: Chart height in pixels
    
    Returns:
        Plotly Figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add Call OI bars
    fig.add_trace(go.Bar(
        x=df['strike'],
        y=df['call_oi'],
        name='CALL',
        marker_color='#1f77b4',
        opacity=0.9,
        hovertemplate='Strike: %{x}<br>Call OI: %{y:,.0f}<extra></extra>'
    ))
    
    # Add Put OI bars
    fig.add_trace(go.Bar(
        x=df['strike'],
        y=df['put_oi'],
        name='PUT',
        marker_color='#ff7f0e',
        opacity=0.9,
        hovertemplate='Strike: %{x}<br>Put OI: %{y:,.0f}<extra></extra>'
    ))
    
    # Add vertical lines for weighted averages and spot price
    # Use scatter traces with mode='lines' to show in legend instead of annotations
    
    # Spot price - purple dashed line
    fig.add_trace(go.Scatter(
        x=[result.spot_price, result.spot_price],
        y=[0, df[['call_oi', 'put_oi']].max().max() * 1.1],
        mode='lines',
        name=f'Spot {symbol}: {result.spot_price:.2f}',
        line=dict(dash='dash', color='purple', width=2),
        showlegend=True,
        hoverinfo='skip'
    ))
    
    # Call weighted average - green dashed line
    if result.call_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result.call_wgt_avg, result.call_wgt_avg],
            y=[0, df[['call_oi', 'put_oi']].max().max() * 1.1],
            mode='lines',
            name=f'Call WgtAvg: {result.call_wgt_avg:.1f}',
            line=dict(dash='dash', color='green', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # Put weighted average - red dashed line
    if result.put_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result.put_wgt_avg, result.put_wgt_avg],
            y=[0, df[['call_oi', 'put_oi']].max().max() * 1.1],
            mode='lines',
            name=f'Put WgtAvg: {result.put_wgt_avg:.1f}',
            line=dict(dash='dash', color='red', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # All weighted average - dark red/brown dashed line
    if result.all_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result.all_wgt_avg, result.all_wgt_avg],
            y=[0, df[['call_oi', 'put_oi']].max().max() * 1.1],
            mode='lines',
            name=f'All WgtAvg: {result.all_wgt_avg:.1f}',
            line=dict(dash='dash', color='darkred', width=2),
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # Update layout - legend positioned in upper right with all items
    fig.update_layout(
        title=f"{symbol} {expiry_date} OI Distribution (by Strike Price)",
        xaxis_title="Strike Price",
        yaxis_title="Open Interest (OI)",
        barmode='group',
        height=height,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(r=50, t=80)
    )
    
    # Format x-axis to show all strike prices
    fig.update_xaxes(
        tickmode='linear',
        tick0=df['strike'].min(),
        dtick=5,
        tickangle=45
    )
    
    # Format y-axis with comma separators
    fig.update_yaxes(
        tickformat=',.0f'
    )
    
    return fig

def create_dual_oi_charts(
    df1: pd.DataFrame,
    result1: WeightedAverageResult,
    expiry_date1: str,
    df2: pd.DataFrame,
    result2: WeightedAverageResult,
    expiry_date2: str,
    symbol: str,
    height: int = 800
) -> go.Figure:
    """
    Create two OI distribution charts stacked vertically
    
    Args:
        df1: DataFrame for first expiry date
        result1: WeightedAverageResult for first expiry
        expiry_date1: First expiry date string
        df2: DataFrame for second expiry date
        result2: WeightedAverageResult for second expiry
        expiry_date2: Second expiry date string
        symbol: Stock symbol
        height: Total chart height
    
    Returns:
        Plotly Figure with two subplots
    """
    # Create subplots
    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=(
            f"{symbol} {expiry_date1} OI Distribution (by Strike Price)",
            f"{symbol} {expiry_date2} OI Distribution (by Strike Price)"
        ),
        vertical_spacing=0.15
    )
    
    max_y1 = df1[['call_oi', 'put_oi']].max().max() * 1.1
    max_y2 = df2[['call_oi', 'put_oi']].max().max() * 1.1
    
    # First subplot
    # Call bars
    fig.add_trace(go.Bar(
        x=df1['strike'],
        y=df1['call_oi'],
        name='CALL',
        marker_color='#1f77b4',
        opacity=0.9,
        showlegend=True,
        legendgroup='group1'
    ), row=1, col=1)
    
    # Put bars
    fig.add_trace(go.Bar(
        x=df1['strike'],
        y=df1['put_oi'],
        name='PUT',
        marker_color='#ff7f0e',
        opacity=0.9,
        showlegend=True,
        legendgroup='group1'
    ), row=1, col=1)
    
    # Add vertical lines for first chart as scatter traces
    fig.add_trace(go.Scatter(
        x=[result1.spot_price, result1.spot_price],
        y=[0, max_y1],
        mode='lines',
        name=f'Spot: {result1.spot_price:.2f}',
        line=dict(dash='dash', color='purple', width=2),
        showlegend=True,
        hoverinfo='skip'
    ), row=1, col=1)
    
    if result1.call_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result1.call_wgt_avg, result1.call_wgt_avg],
            y=[0, max_y1],
            mode='lines',
            name=f'Call WgtAvg: {result1.call_wgt_avg:.1f}',
            line=dict(dash='dash', color='green', width=2),
            showlegend=True,
            hoverinfo='skip'
        ), row=1, col=1)
    
    if result1.put_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result1.put_wgt_avg, result1.put_wgt_avg],
            y=[0, max_y1],
            mode='lines',
            name=f'Put WgtAvg: {result1.put_wgt_avg:.1f}',
            line=dict(dash='dash', color='red', width=2),
            showlegend=True,
            hoverinfo='skip'
        ), row=1, col=1)
    
    # Second subplot
    # Call bars
    fig.add_trace(go.Bar(
        x=df2['strike'],
        y=df2['call_oi'],
        name='CALL',
        marker_color='#1f77b4',
        opacity=0.9,
        showlegend=False,
        legendgroup='group1'
    ), row=2, col=1)
    
    # Put bars
    fig.add_trace(go.Bar(
        x=df2['strike'],
        y=df2['put_oi'],
        name='PUT',
        marker_color='#ff7f0e',
        opacity=0.9,
        showlegend=False,
        legendgroup='group1'
    ), row=2, col=1)
    
    # Add vertical lines for second chart
    fig.add_trace(go.Scatter(
        x=[result2.spot_price, result2.spot_price],
        y=[0, max_y2],
        mode='lines',
        name=f'Spot: {result2.spot_price:.2f}',
        line=dict(dash='dash', color='purple', width=2),
        showlegend=False,
        hoverinfo='skip'
    ), row=2, col=1)
    
    if result2.call_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result2.call_wgt_avg, result2.call_wgt_avg],
            y=[0, max_y2],
            mode='lines',
            name=f'Call WgtAvg: {result2.call_wgt_avg:.1f}',
            line=dict(dash='dash', color='green', width=2),
            showlegend=False,
            hoverinfo='skip'
        ), row=2, col=1)
    
    if result2.put_wgt_avg > 0:
        fig.add_trace(go.Scatter(
            x=[result2.put_wgt_avg, result2.put_wgt_avg],
            y=[0, max_y2],
            mode='lines',
            name=f'Put WgtAvg: {result2.put_wgt_avg:.1f}',
            line=dict(dash='dash', color='red', width=2),
            showlegend=False,
            hoverinfo='skip'
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        height=height,
        barmode='group',
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(r=50)
    )
    
    # Update y-axes
    fig.update_yaxes(title_text="Open Interest (OI)", tickformat=',.0f', row=1, col=1)
    fig.update_yaxes(title_text="Open Interest (OI)", tickformat=',.0f', row=2, col=1)
    
    # Update x-axes
    fig.update_xaxes(title_text="Strike Price", tickangle=45, row=2, col=1)
    
    return fig

def create_metrics_cards(result: WeightedAverageResult, symbol: str) -> str:
    """
    Create HTML metrics cards showing key statistics
    
    Returns:
        HTML string for metrics display
    """
    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; color: white; flex: 1; min-width: 150px;">
            <div style="font-size: 12px; opacity: 0.9;">Spot Price</div>
            <div style="font-size: 24px; font-weight: bold;">{result.spot_price:.2f}</div>
            <div style="font-size: 11px;">{symbol}</div>
        </div>
        
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 15px; border-radius: 10px; color: white; flex: 1; min-width: 150px;">
            <div style="font-size: 12px; opacity: 0.9;">Call WgtAvg</div>
            <div style="font-size: 24px; font-weight: bold;">{result.call_wgt_avg:.2f}</div>
            <div style="font-size: 11px;">OI: {result.call_total_oi:,}</div>
        </div>
        
        <div style="background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%); 
                    padding: 15px; border-radius: 10px; color: white; flex: 1; min-width: 150px;">
            <div style="font-size: 12px; opacity: 0.9;">Put WgtAvg</div>
            <div style="font-size: 24px; font-weight: bold;">{result.put_wgt_avg:.2f}</div>
            <div style="font-size: 11px;">OI: {result.put_total_oi:,}</div>
        </div>
        
        <div style="background: linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%); 
                    padding: 15px; border-radius: 10px; color: white; flex: 1; min-width: 150px;">
            <div style="font-size: 12px; opacity: 0.9;">All WgtAvg</div>
            <div style="font-size: 24px; font-weight: bold;">{result.all_wgt_avg:.2f}</div>
            <div style="font-size: 11px;">Total OI: {result.all_total_oi:,}</div>
        </div>
    </div>
    """
    return html


def create_oi_trend_chart(
    trend_data: pd.DataFrame,
    symbol: str,
    spot_price: float,
    height: int = 600
) -> go.Figure:
    """
    Create OI trend chart showing Call WgtAvg, Put WgtAvg, All WgtAvg over expiry dates
    
    Args:
        trend_data: DataFrame with columns ['expiry_date', 'call_wgt_avg', 'put_wgt_avg', 'all_wgt_avg']
        symbol: Stock symbol
        spot_price: Current spot price
        height: Chart height in pixels
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    # Add Call WgtAvg line - green
    fig.add_trace(go.Scatter(
        x=trend_data['expiry_date'],
        y=trend_data['call_wgt_avg'],
        mode='lines+markers',
        name='Call WgtAvg',
        line=dict(color='green', width=3),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='到期日: %{x}<br>Call WgtAvg: %{y:.2f}<extra></extra>'
    ))
    
    # Add Put WgtAvg line - red
    fig.add_trace(go.Scatter(
        x=trend_data['expiry_date'],
        y=trend_data['put_wgt_avg'],
        mode='lines+markers',
        name='Put WgtAvg',
        line=dict(color='red', width=3),
        marker=dict(size=8, symbol='circle'),
        hovertemplate='到期日: %{x}<br>Put WgtAvg: %{y:.2f}<extra></extra>'
    ))
    
    # Add All WgtAvg line - dark red/brown
    fig.add_trace(go.Scatter(
        x=trend_data['expiry_date'],
        y=trend_data['all_wgt_avg'],
        mode='lines+markers',
        name='All WgtAvg',
        line=dict(color='darkred', width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond'),
        hovertemplate='到期日: %{x}<br>All WgtAvg: %{y:.2f}<extra></extra>'
    ))
    
    # Add Spot price horizontal line - purple
    fig.add_trace(go.Scatter(
        x=[trend_data['expiry_date'].iloc[0], trend_data['expiry_date'].iloc[-1]],
        y=[spot_price, spot_price],
        mode='lines',
        name=f'Spot {symbol}: {spot_price:.2f}',
        line=dict(color='purple', width=2, dash='dot'),
        hoverinfo='skip'
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} OI 走势图 (加权平均价趋势)",
        xaxis_title="到期日",
        yaxis_title="Strike Price",
        height=height,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            font=dict(size=12)
        ),
        margin=dict(r=50, t=80, b=80),
        hovermode='x unified'
    )
    
    # Format x-axis
    fig.update_xaxes(
        tickangle=45,
        type='category'
    )
    
    # Format y-axis
    fig.update_yaxes(
        tickformat='.2f'
    )
    
    return fig
