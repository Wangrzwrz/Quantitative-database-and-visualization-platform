import streamlit as st
import plotly.graph_objects as go
from QuantDB import QuantDB

@st.cache_resource
def get_db_connection():
    """
    初始化并缓存数据库连接单例。
    配置信息通过 Streamlit secrets 或默认参数获取。
    """
    # 建议生产环境下使用 st.secrets["db_password"] 代替硬编码
    return QuantDB(
        host='localhost',
        port=8123,
        user='default',
        password=''
    )

def init_page_config(page_title="Quant Platform"):
    """
    统一初始化页面布局与全局样式。
    """
    st.set_page_config(
        page_title=page_title,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 注入全局 CSS 以优化组件间距与视觉密度
    st.markdown("""
        <style>
            .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
            div[data-testid="stMetricValue"] {font-size: 1.1rem; font-weight: 600;}
            section[data-testid="stSidebar"] {background-color: #f8f9fa;}
        </style>
    """, unsafe_allow_html=True)

def plot_kline(df, title="Stock Price Analysis"):
    """
    基于 Plotly 绘制交互式 K 线图。
    """
    fig = go.Figure(data=[go.Candlestick(
        x=df['trade_date'],
        open=df['open'], 
        high=df['high'],
        low=df['low'], 
        close=df['close'],
        name='Price',
        increasing_line_color='#ef5350', 
        decreasing_line_color='#26a69a'  
    )])
    
    fig.update_layout(
        title={
            'text': title,
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        yaxis_title='Price (CNY)',
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=10, r=10, t=50, b=10),
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig