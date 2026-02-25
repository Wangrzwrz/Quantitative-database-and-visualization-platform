import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_db_connection

st.set_page_config(page_title="行业轮动量化面板", layout="wide")
db = get_db_connection()

# ================= 1. 全局状态管理 =================
if 'global_date' not in st.session_state:
    st.session_state['global_date'] = db.get_latest_trade_date()

st.title("行业景气度与轮动量化分析")
st.caption("研究框架：基于申万二级行业 (SW2) 分类体系，通过截面动量、估值水平及流动性特征进行资产定价分析。")

with st.sidebar:
    st.header("控制中心")
    picked_date = st.date_input("分析基准日", value=st.session_state['global_date'])
    if picked_date != st.session_state['global_date']:
        st.session_state['global_date'] = picked_date
        st.rerun()
    date_str = str(st.session_state['global_date'])

# ================= 2. 行业数据加载 =================
@st.cache_data(ttl=600)
def load_sector_data(target_date):
    """
    调取指定日期的行业截面汇总数据。
    包含：动量指标、估值指标、成交活跃度及技术强度。
    """
    return db.get_sector_rotation_rank(target_date)

try:
    with st.spinner(f"正在聚合 {date_str} 行业截面数据..."):
        df_sec = load_sector_data(date_str)
    
    if df_sec.empty:
        st.error("指定日期无有效交易数据，请调整参数。")
        st.stop()

    df_sec = df_sec.dropna(subset=['avg_mom_20', 'median_pe', 'total_amt_yi'])

    df_sec_valid = df_sec[(df_sec['median_pe'] > 0) & (df_sec['median_pe'] < 100)]

except Exception as e:
    st.error(f"数据处理模块异常: {e}")
    st.stop()

# ================= 3. 行业攻守象限分析 =================
st.subheader("行业配置象限图")

c_chart, c_ctrl = st.columns([4, 1])

with c_ctrl:
    st.markdown("### 量化指标释义")
    st.markdown("""
    - **横轴 (X-Axis)**: 20日截面平均收益率(动量特征)。
    - **纵轴 (Y-Axis)**: PE (TTM) 中位数(估值水平)。
    - **气泡半径**: 日成交金额(流动性强度)。
    - **色阶变化**: 14日 RSI 指标(技术超买/超卖程度)。
    """)
    st.divider()
    pe_limit = st.slider("估值轴上限", 20, 100, 60)

with c_chart:
    plot_df = df_sec[(df_sec['median_pe'] > 0) & (df_sec['median_pe'] <= pe_limit)]
    
    fig = px.scatter(
        plot_df,
        x="avg_mom_20", 
        y="median_pe",
        size="total_amt_yi",
        color="avg_rsi",
        hover_name="sector_name",
        text="sector_name",
        color_continuous_scale="RdYlBu_r", 
        labels={
            "avg_mom_20": "月动量 (Momentum %)",
            "median_pe": "估值中位数 (PE TTM)",
            "total_amt_yi": "流动性 (Amount, 100M CNY)",
            "avg_rsi": "RSI(14)"
        },
        title=f"行业景气度分布截面 ({date_str})"
    )

    median_x = plot_df['avg_mom_20'].median()
    median_y = plot_df['median_pe'].median()
    fig.add_hline(y=median_y, line_dash="dash", line_color="rgba(128,128,128,0.5)", annotation_text="中位估值")
    fig.add_vline(x=median_x, line_dash="dash", line_color="rgba(128,128,128,0.5)", annotation_text="中位动量")
    
    fig.update_traces(textposition='top center')
    fig.update_layout(height=600, template="plotly_white", margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ================= 4. 行业排名与资产穿透 =================
c_list, c_detail = st.columns([4, 6])

with c_list:
    st.subheader("行业综合排行榜")
    st.caption("交互提示：通过选择表格行可触发行穿透分析，研究特定行业的历史趋势与权重成分。")

    sort_mapping = {
        'avg_pct_chg': '日收益率', 
        'total_amt_yi': '成交金额', 
        'avg_mom_20': '月动量强度', 
        'median_pe': 'PE估值水平', 
        'avg_turnover': '换手率'
    }
    sort_col = st.selectbox("排序维度选择", list(sort_mapping.keys()), format_func=lambda x: sort_mapping[x])
    ascending_order = st.checkbox("升序排列", value=True if sort_col == 'median_pe' else False) 

    display_df = df_sec.sort_values(sort_col, ascending=ascending_order).reset_index(drop=True)

    event = st.dataframe(
        display_df[['sector_name', 'avg_pct_chg', 'total_amt_yi', 'median_pe', 'avg_mom_20', 'stock_count']],
        column_config={
            "sector_name": "行业板块",
            "avg_pct_chg": st.column_config.NumberColumn("日涨跌幅", format="%.2f%%"),
            "total_amt_yi": st.column_config.NumberColumn("成交额(亿)", format="%.1f"),
            "median_pe": st.column_config.NumberColumn("PE(中位)", format="%.1f"),
            "avg_mom_20": st.column_config.NumberColumn("20D动量", format="%.1f%%"),
            "stock_count": st.column_config.NumberColumn("样本量")
        },
        use_container_width=True, height=500, hide_index=True,
        selection_mode="single-row", on_select="rerun" 
    )

    sector_list = display_df['sector_name'].tolist()
    with st.expander("行业板块精确检索", expanded=False):
        manual_sector = st.selectbox("选择或搜索:", sector_list, index=0)

    final_sector = None
    if event.selection.rows:
        final_sector = display_df.iloc[event.selection.rows[0]]['sector_name']
    elif manual_sector:
        final_sector = manual_sector
    elif not display_df.empty:
        final_sector = display_df.iloc[0]['sector_name']

with c_detail:
    if final_sector:
        st.subheader(f"行业纵向穿透: {final_sector}")

        with st.spinner("检索行业指数历史序列..."):
            df_hist = db.get_sector_index_history(final_sector, date_str, days=60)
        
        if not df_hist.empty:
            df_hist.columns = [c.split('.')[-1] for c in df_hist.columns]
            df_hist['trade_date'] = pd.to_datetime(df_hist.get('trade_date', df_hist.index)).dt.tz_localize(None)
            df_hist['equity'] = (1 + df_hist['sector_chg']/100).cumprod()
            
            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
            fig_trend.add_trace(go.Scatter(x=df_hist['trade_date'], y=df_hist['equity'], 
                                         name="板块指数", line=dict(color='#c62828', width=2)), secondary_y=False)
            fig_trend.add_trace(go.Scatter(x=df_hist['trade_date'], y=df_hist['sector_pe'], 
                                         name="板块PE", line=dict(color='#455a64', dash='dot')), secondary_y=True)
            
            fig_trend.update_layout(
                height=350, margin=dict(t=30, b=10, l=10, r=10), 
                hovermode='x unified', title_text="60个交易日价格净值与估值演变", template="plotly_white"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("该行业板块暂未建立完整历史指数序列。")
        
        st.divider()

        st.markdown(f"**{final_sector} 核心成分股 (Top Constituents)**")
        df_cons = db.get_sector_constituents(date_str, final_sector) 
        
        if not df_cons.empty:
            df_cons.columns = [c.split('.')[-1] for c in df_cons.columns]

            grid_cols = st.columns(3)
            for i, row in enumerate(df_cons.head(6).itertuples()):
                with grid_cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{row.stock_name}**")
                        color_val = "#c62828" if row.pct_chg > 0 else "#2e7d32"
                        st.markdown(f"`{row.stock_code}` | <span style='color:{color_val}'>{row.pct_chg:.2f}%</span>", unsafe_allow_html=True)
                        st.caption(f"现价: {row.close} | PE: {row.pe_ttm:.1f}")
                        
                        if st.button("深度研判", key=f"btn_{row.stock_code}"):
                            st.session_state['selected_stock'] = row.stock_code
                            st.switch_page("pages/4_Stock deepdive.py")
            
            if len(df_cons) > 6:
                with st.expander("查看全量行业成分股列表"):
                    st.dataframe(
                        df_cons[['stock_code', 'stock_name', 'pct_chg', 'close', 'amount', 'pe_ttm']], 
                        column_config={
                            "stock_code": "证券代码", "stock_name": "名称",
                            "pct_chg": st.column_config.NumberColumn("日涨幅", format="%.2f%%"),
                            "amount": st.column_config.NumberColumn("成交额(元)", format="%.0f"),
                            "pe_ttm": st.column_config.NumberColumn("PE(TTM)", format="%.1f")
                        },
                        hide_index=True, use_container_width=True
                    )
        else:
            st.info("该行业成分股数据尚未完成穿透处理。")