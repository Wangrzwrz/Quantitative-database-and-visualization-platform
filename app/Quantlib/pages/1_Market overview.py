import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import get_db_connection

# 页面基础配置：采用宽屏模式
st.set_page_config(page_title="市场综述 - 宏观量化全景", layout="wide")
db = get_db_connection()

# ================= 1. 全局状态初始化 =================
if 'global_date' not in st.session_state:
    st.session_state['global_date'] = db.get_latest_trade_date()

st.title("市场全景概论")

with st.sidebar:
    st.header("参数配置)")
    # 日期锚点选择，用于回溯历史交易日断面
    picked_date = st.date_input("分析基准日", value=st.session_state['global_date'])
    if picked_date != st.session_state['global_date']:
        st.session_state['global_date'] = picked_date
        st.rerun()

date_str = str(st.session_state['global_date'])

# ================= 2. 宏观统计指标 =================
stats = db.get_market_general_stats(date_str)
c1, c2, c3 = st.columns(3)

amt_val = stats['total_amt']
amt_diff = amt_val - stats['prev_amt']

c1.metric("全A市场成交总额", f"{amt_val/1e8:.2f} 亿", 
          f"{'+' if amt_diff > 0 else ''}{amt_diff/1e8:.2f} 亿 (YoY)", 
          delta_color="off")

c2.metric("涨跌幅中位数", f"{stats['median_chg']:.2f}%", 
          "市场中性情绪指标", 
          delta_color="normal" if stats['median_chg'] > 0 else "inverse")

c3.metric("市场涨跌占比", f"升 {stats['up_count']} / 降 {stats['down_count']}", 
          f"净变动 {stats['up_count'] - stats['down_count']}", 
          delta_color="normal" if stats['up_count'] > stats['down_count'] else "inverse")

st.divider()

# ================= 3. 核心指数 =================
st.subheader("核心指数实时概览")
df_index = db.get_market_index_daily(date_str)

target_indices = {
    '000001.SH': '上证指数', '399001.SZ': '深证成指', '399006.SZ': '创业板指',
    '000688.SH': '科创50', '000016.SH': '上证50', '000905.SH': '中证500', '000852.SH': '中证1000'
}

if not df_index.empty:
    cols = st.columns(len(target_indices))
    for i, (code, name) in enumerate(target_indices.items()):
        row = df_index[df_index['stock_code'] == code]
        with cols[i]:
            if not row.empty:
                curr_price = row.iloc[0]['close']
                pct_change = row.iloc[0]['pct_chg']
                st.metric(name, f"{curr_price:.2f}", f"{pct_change:.2f}%", 
                          delta_color="normal" if pct_change >= 0 else "inverse")
            else:
                st.metric(name, "N/A", "N/A")
else:
    st.info("系统提示：指数截面数据缺失")

st.divider()

# ================= 4. 趋势收敛与收益分布 =================
c_chart, c_dist = st.columns([6, 4])

with c_chart:
    st.subheader("指数累计收益率走势 (归一化)")
    df_hist = db.get_market_index_history(date_str, days=30)
    if not df_hist.empty:
        df_hist['normalized'] = df_hist.groupby('stock_code')['close'].transform(lambda x: x / x.iloc[0] - 1)
        fig_line = px.line(
            df_hist, x='trade_date', y='normalized', color='stock_name',
            color_discrete_map={'上证指数': '#e74c3c', '创业板指': '#3498db', '科创50': '#9b59b6'}
        )
        fig_line.update_yaxes(tickformat=".1%")
        fig_line.update_layout(
            height=350, margin=dict(l=0, r=0, t=30, b=0), 
            hovermode="x unified", xaxis_title=None, yaxis_title="累计超额收益率"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("数据分析：历史序列样本不足")

with c_dist:
    st.subheader("个股涨跌幅频数分布")
    df_snap = db.get_market_snapshot(date_str)
    if not df_snap.empty:
        bins = [-100, -9.8, -7, -5, -3, 0, 3, 5, 7, 9.8, 100]
        labels = ['跌停', '-7%', '-5%', '-3%', '跌', '涨', '3%', '5%', '7%', '涨停']
        cuts = pd.cut(df_snap['pct_chg'], bins=bins, labels=labels)
        distribution = cuts.value_counts().sort_index()

        colors = ['#1a5e20', '#2e7d32', '#43a047', '#66bb6a', '#a5d6a7', 
                  '#ef9a9a', '#ef5350', '#e53935', '#c62828', '#b71c1c']
        
        fig_bar = go.Figure(go.Bar(
            x=distribution.index, y=distribution.values, 
            text=distribution.values, textposition='outside', 
            marker_color=colors
        ))
        fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="频数 (Count)")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("数据分析：截面分布数据缺失")

st.divider()

# ================= 5. 行业结构与权重分析 =================
st.subheader("产业板块结构化热力透视")
df_sector = db.get_sector_data_enhanced(date_str)

if not df_sector.empty:
    c_heat, c_detail = st.columns([5, 3])
    
    with c_heat:
        st.caption("注：矩形面积代表成交热度, 颜色深度反映涨跌振幅")
        fig_tree = px.treemap(
            df_sector, path=['name'], values='heat', color='pct_chg',
            color_continuous_scale=['#2ecc71', '#ecf0f1', '#e74c3c'], color_continuous_midpoint=0,
            custom_data=['pct_chg', 'rank']
        )
        fig_tree.update_traces(
            hovertemplate='<b>行业名称: %{label}</b><br>收益率: %{customdata[0]:.2f}%<br>成交热度: %{value:.0f}'
        )
        fig_tree.update_layout(height=550, margin=dict(t=0, l=0, r=0, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)
        
    with c_detail:
        sector_list = df_sector['name'].tolist()
        selected_sector = st.selectbox("行业细分板块检索", sector_list, index=0)
        st.markdown(f"**板块分析报告：{selected_sector} 核心权重股**")

        df_cons = db.get_sector_constituents(date_str, selected_sector)
        
        if not df_cons.empty:
            st.dataframe(
                df_cons[['stock_name', 'stock_code', 'pct_chg', 'close', 'amount', 'pe_ttm']],
                column_config={
                    "stock_name": "名称", 
                    "stock_code": "代码",
                    "pct_chg": st.column_config.NumberColumn("收益率", format="%.2f%%"),
                    "close": st.column_config.NumberColumn("收盘价", format="%.2f"),
                    "amount": st.column_config.ProgressColumn("成交额", format="¥%.0f", max_value=df_cons['amount'].max()),
                    "pe_ttm": st.column_config.NumberColumn("市盈率(TTM)", format="%.1f")
                },
                height=480, 
                hide_index=True, 
                use_container_width=True
            )
        else:
            st.warning("结果提示：未能检索到行业成分股明细")
else:
    st.info("系统提示：当前断面无行业热度数据")