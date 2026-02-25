import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_db_connection

st.set_page_config(page_title="个股深度研究", layout="wide")
db = get_db_connection()

st.title("个股深度研究")

# ================= 1. 基础数据加载=================
with st.sidebar:
    st.header("资产检索与参数配置")
    default_code = st.session_state.get('selected_stock', '000001.SZ')
    stock_code = st.text_input("证券代码", value=default_code)
    st.session_state['selected_stock'] = stock_code

    info = db.get_stock_info(stock_code)
    st.markdown(f"### {info['name']}")
    st.caption(f"行业归属: {info['industry']} | 注册地: {info['area']}")

    min_date, max_date = db.get_stock_available_range(stock_code)
    if min_date and max_date:
        default_start = max_date - pd.Timedelta(days=365)
        if default_start < min_date: 
            default_start = min_date
        start_date = st.date_input("研究起点", default_start, min_value=min_date, max_value=max_date)
        end_date = st.date_input("研究终点", max_date, min_value=min_date, max_value=max_date)
    else:
        st.error("证券数据检索失败：无有效成交记录")
        st.stop()

if 'stock_df_cache' not in st.session_state or \
   st.session_state.get('cached_code') != stock_code or \
   st.session_state.get('cached_start') != str(start_date) or \
   st.session_state.get('cached_end') != str(end_date):
    
    with st.spinner("正在检索基础行情序列..."):
        df_base = db.get_stock_base_kline(stock_code, str(start_date), str(end_date))
        df_base['trade_date'] = pd.to_datetime(df_base['trade_date']).dt.tz_localize(None)
        for c in ['open','close','high','low','vol','pct_chg']: 
            df_base[c] = pd.to_numeric(df_base[c], errors='coerce')
        
        st.session_state['stock_df_cache'] = df_base
        st.session_state['cached_code'] = stock_code
        st.session_state['cached_start'] = str(start_date)
        st.session_state['cached_end'] = str(end_date)

df = st.session_state['stock_df_cache']

# ================= 2. 动态因子获取逻辑 =================
c_main_opt, c_sub_opt = st.columns([1, 1])
with c_main_opt:
    main_overlays = st.multiselect("主图分析", ['MA (均线)', 'BOLL (布林带)', '价格极值标记'], default=['MA (均线)'])
with c_sub_opt:
    sub_indicator = st.selectbox("副图指标", [
        'MACD', 'KDJ', 'RSI', 'WR', 'CCI', 'BIAS', 
        'MFI', 'Volatility', 'Turnover', 
        'PE_TTM', 'Z-Score', 'Sentiment'
    ])

INDICATOR_MAP = {
    'MA (均线)': {'table': 'factor_technical_daily', 'cols': ['ma_5', 'ma_20', 'ma_60']},
    'BOLL (布林带)': {'table': 'factor_technical_daily', 'cols': ['boll_upper', 'boll_lower']},
    'MACD': {'table': 'factor_technical_daily', 'cols': ['macd_diff', 'macd_dea']},
    'KDJ': {'table': 'factor_technical_daily', 'cols': ['kdj_k', 'kdj_d', 'kdj_j']},
    'RSI': {'table': 'factor_technical_daily', 'cols': ['rsi_14']},
    'WR (威廉)': {'table': 'factor_technical_daily', 'cols': ['wr_14']},
    'CCI (顺势)': {'table': 'factor_technical_daily', 'cols': ['cci_14']},
    'BIAS (乖离)': {'table': 'factor_technical_daily', 'cols': ['bias_20']},
    'MFI (资金流量)': {'table': 'factor_technical_daily', 'cols': ['mfi_14']},
    'Volatility (波动率)': {'table': 'factor_momentum_daily', 'cols': ['volatility_20']},
    'PE_TTM (估值)': {'table': 'stock_fundamental_daily', 'cols': ['pe_ttm'], 'db': 'quant_db'}, 
    'Z-Score (估值分位)': {'table': 'factor_value_daily', 'cols': ['pe_zscore_60', 'pb_zscore_60']},
    'Sentiment (封单)': {'table': 'factor_sentiment_daily', 'cols': ['kpl_seal_money', 'is_limit_up', 'is_limit_broken']},
    '涨停/炸板标记': {'table': 'factor_sentiment_daily', 'cols': ['is_limit_up', 'is_limit_broken', 'kpl_seal_money']}
}

missing_fields_config = []
required_indicators = [sub_indicator] if sub_indicator != 'Turnover (换手率)' else []
required_indicators.extend(main_overlays)

for ind in required_indicators:
    if ind in INDICATOR_MAP:
        cfg = INDICATOR_MAP[ind]
        missing_cols = [c for c in cfg['cols'] if c not in df.columns]
        if missing_cols:
            config_item = {'table': cfg['table'], 'cols': cfg['cols']}
            if 'db' in cfg: config_item['db'] = cfg['db']
            missing_fields_config.append(config_item)

if missing_fields_config:
    with st.spinner(f"正在调取因子库: {sub_indicator} ..."):
        df_new = db.get_stock_dynamic_indicators(stock_code, str(start_date), str(end_date), missing_fields_config)
        df_new['trade_date'] = pd.to_datetime(df_new['trade_date']).dt.tz_localize(None)
        for c in df_new.columns:
            if c != 'trade_date': df_new[c] = pd.to_numeric(df_new[c], errors='coerce')
            
        df = pd.merge(df, df_new, on='trade_date', how='left', suffixes=('', '_new'))
        for col in list(df.columns):
            if col.endswith('_new'):
                original = col[:-4]
                df[original] = df[col]
                del df[col]
        st.session_state['stock_df_cache'] = df

# ================= 3. 高级交互可视化 =================
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, 
                    row_heights=[0.6, 0.1, 0.3], 
                    subplot_titles=(f"{info['name']} ({stock_code}) - Price Action", "Volume", f"{sub_indicator} Analysis"))

# 主图 K线
fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], 
                             name="K线序列", increasing_line_color='#c62828', decreasing_line_color='#2e7d32'), row=1, col=1)

# 叠加主图指标
if 'MA (均线)' in main_overlays:
    for ma in [5, 20, 60]:
        if f'ma_{ma}' in df.columns: 
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df[f'ma_{ma}'], name=f'MA{ma}', line=dict(width=1.2)), row=1, col=1)
if 'BOLL (布林带)' in main_overlays and 'boll_upper' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['boll_upper'], line=dict(width=1, dash='dot', color='rgba(100,100,100,0.5)'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['boll_lower'], line=dict(width=1, dash='dot', color='rgba(100,100,100,0.5)'), 
                             fill='tonexty', fillcolor='rgba(128,128,128,0.05)', name='BOLL通道'), row=1, col=1)
if '涨停/炸板标记' in main_overlays:
    if 'is_limit_up' in df.columns:
        limit_ups = df[df['is_limit_up'] == 1]
        if not limit_ups.empty: 
            fig.add_trace(go.Scatter(x=limit_ups['trade_date'], y=limit_ups['high']*1.02, mode='markers', 
                                     marker=dict(symbol='triangle-down', size=8, color='#b71c1c'), name='价格上限触达'), row=1, col=1)
    if 'is_limit_broken' in df.columns:
        broken = df[df['is_limit_broken'] == 1]
        if not broken.empty: 
            fig.add_trace(go.Scatter(x=broken['trade_date'], y=broken['high']*1.02, mode='markers', 
                                     marker=dict(symbol='x', size=6, color='#212121'), name='高位承接失败'), row=1, col=1)

# 流动性
volume_colors = ['#c62828' if r.close >= r.open else '#2e7d32' for i, r in df.iterrows()]
fig.add_trace(go.Bar(x=df['trade_date'], y=df['vol'], marker_color=volume_colors, name="成交量"), row=2, col=1)

# 副图
if sub_indicator == 'MACD' and 'macd_diff' in df.columns:
    df['macd_hist'] = (df['macd_diff'] - df['macd_dea']) * 2
    fig.add_trace(go.Bar(x=df['trade_date'], y=df['macd_hist'], marker_color=['#e74c3c' if x>0 else '#2ecc71' for x in df['macd_hist'].fillna(0)], name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd_diff'], name='DIFF'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd_dea'], name='DEA'), row=3, col=1)
elif sub_indicator == 'KDJ' and 'kdj_k' in df.columns:
    for k in ['k','d','j']: fig.add_trace(go.Scatter(x=df['trade_date'], y=df[f'kdj_{k}'], name=k.upper()), row=3, col=1)
elif sub_indicator == 'RSI' and 'rsi_14' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['rsi_14'], name='RSI14'), row=3, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=3, col=1); fig.add_hline(y=20, line_dash="dash", line_color="green", row=3, col=1)
elif sub_indicator == 'WR (威廉)' and 'wr_14' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['wr_14'], name='WR14'), row=3, col=1)
    fig.add_hline(y=-20, line_dash="dash", line_color="red", row=3, col=1); fig.add_hline(y=-80, line_dash="dash", line_color="green", row=3, col=1)
elif sub_indicator == 'CCI (顺势)' and 'cci_14' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['cci_14'], name='CCI'), row=3, col=1)
    fig.add_hline(y=100, line_dash="dash", line_color="red", row=3, col=1); fig.add_hline(y=-100, line_dash="dash", line_color="green", row=3, col=1)
elif sub_indicator == 'BIAS (乖离)' and 'bias_20' in df.columns:
    fig.add_trace(go.Bar(x=df['trade_date'], y=df['bias_20'], name='BIAS20'), row=3, col=1)
elif sub_indicator == 'MFI (资金流量)' and 'mfi_14' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['mfi_14'], name='MFI', fill='tozeroy'), row=3, col=1)
elif sub_indicator == 'Volatility (波动率)' and 'volatility_20' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['volatility_20'], name='Vol20', line=dict(color='black')), row=3, col=1)
elif sub_indicator == 'Turnover (换手率)':
    fig.add_trace(go.Bar(x=df['trade_date'], y=df['turnover_rate'], name='换手%', marker_color='#f39c12'), row=3, col=1)
elif sub_indicator == 'PE_TTM (估值)' and 'pe_ttm' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['pe_ttm'], name='PE', line=dict(color='orange'), fill='tozeroy'), row=3, col=1)
elif sub_indicator == 'Z-Score (估值分位)' and 'pe_zscore_60' in df.columns:
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['pe_zscore_60'], name='PE Z-Score', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['trade_date'], y=df['pb_zscore_60'], name='PB Z-Score', line=dict(color='orange')), row=3, col=1)
    fig.add_hline(y=0, line_color="black", row=3, col=1)
elif sub_indicator == 'Sentiment (封单)' and 'kpl_seal_money' in df.columns:
    fig.add_trace(go.Bar(x=df['trade_date'], y=df['kpl_seal_money'], name='封单', marker_color='#e74c3c'), row=3, col=1)

fig.update_layout(height=800, xaxis_rangeslider_visible=False, hovermode='x unified', margin=dict(l=10, r=10, t=30, b=10), template="plotly_white")
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# ================= 4. 截面因子透视 =================
st.divider()
c_title, c_slider = st.columns([1, 2])
with c_title:
    st.subheader("截面因子分布透视")
with c_slider:
    available_dates = df['trade_date'].dt.date.sort_values().unique()
    if len(available_dates) > 0:
        selected_date = st.select_slider("截面时间节点选择", options=available_dates, value=available_dates[-1])
    else: 
        st.stop()

# 获取截面因子快照
snap = db.get_stock_factor_snapshot(stock_code, str(selected_date))
if snap:
    tabs = st.tabs(["估值分析", "动量特征", "技术强度", "情绪因子"])
    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PE (TTM)", f"{snap.get('pe_ttm', 0):.2f}")
        c2.metric("PB (LF)", f"{snap.get('pb', 0):.2f}")
        c3.metric("股息收益率", f"{snap.get('dividend_yield', 0):.2f}%")
        c4.metric("净利润同比增长", f"{snap.get('yoy_profit', 0):.1f}%")
    with tabs[1]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("20日收益率", f"{snap.get('roc_20', 0):.2f}%")
        c2.metric("20日年化波动", f"{snap.get('volatility_20', 0):.2f}")
        c3.metric("20日相对价位", f"{snap.get('price_pos_20', 0):.1f}%")
        c4.metric("20日乖离率", f"{snap.get('bias_20', 0):.2f}%")
    with tabs[2]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("RSI (14)", f"{snap.get('rsi_14', 0):.1f}")
        c2.metric("KDJ (J)", f"{snap.get('kdj_j', 0):.1f}")
        c3.metric("CCI (14)", f"{snap.get('cci_14', 0):.1f}")
        c4.metric("WR (14)", f"{snap.get('wr_14', 0):.1f}")
    with tabs[3]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("连板效应", f"{int(snap.get('limit_up_streak', 0))} Day(s)")
        seal = snap.get('kpl_seal_money', 0)
        c2.metric("封单", f"{seal/1e8:.2f}亿" if seal>1e8 else f"{seal/1e4:.0f}万")
        c3.metric("涨停", "True" if snap.get('is_limit_up')==1 else "False")
        c4.metric("主力净流向", f"{snap.get('money_flow_main', 0)/1e4:.0f}万")

# ================= 5. 基本面历史与同业对标 =================
st.divider()
c_fund_table, c_peer = st.columns([1, 1])

with c_fund_table:
    st.subheader("基本面明细")
    df_fund = db.get_stock_fundamentals_history(stock_code, str(start_date), str(end_date))
    st.dataframe(
        df_fund, use_container_width=True, height=400,
        column_config={
            "trade_date": st.column_config.DateColumn("报告日期"),
            "pe_ttm": st.column_config.NumberColumn("PE(TTM)", format="%.2f"),
            "pb": st.column_config.NumberColumn("PB", format="%.2f"),
            "total_mv": st.column_config.NumberColumn("总市值(元)", format="%.0f"),
            "turnover_rate": st.column_config.NumberColumn("换手率(%)", format="%.2f")
        }, hide_index=True
    )

with c_peer:
    st.subheader("同业对标分析")
    st.caption("分析基准：申万二级行业 (SW-L2) | 排序维度：自由流通市值")
    df_peer = db.get_industry_peers_snapshot(stock_code, str(selected_date))
    
    if not df_peer.empty:
        def style_baseline_asset(row):
            return ['background-color: rgba(255, 230, 230, 0.5)'] * len(row) if row['stock_code'] == stock_code else [''] * len(row)

        display_cols = ['stock_code', 'stock_name', 'mv_yi', 'pe_ttm', 'pct_chg', 'roe_ttm']
        st.dataframe(
            df_peer[display_cols].style.apply(style_baseline_asset, axis=1),
            use_container_width=True, height=400,
            column_config={
                "stock_code": "证券代码", "stock_name": "名称",
                "mv_yi": st.column_config.NumberColumn("市值(亿)", format="%.1f"),
                "pe_ttm": st.column_config.NumberColumn("PE(TTM)", format="%.2f"),
                "pct_chg": st.column_config.NumberColumn("收益率", format="%.2f%%"),
                "roe_ttm": st.column_config.NumberColumn("ROE(%)", format="%.2f")
            }, hide_index=True
        )
    else:
        st.info("同业对标数据集为空")

# ================= 6. 相似K线回溯分析 =================

st.divider()
st.subheader("相似K线形态回溯分析")
st.caption("算法逻辑: 基于技术指标(RSI, CCI, BIAS向量)的欧氏距离度量, 在全市场历史库中检索形态最接近的3个样本，分析其后20个交易日的收益表现。")

current_feature_vec = db.get_technical_vector(stock_code, str(selected_date))

if current_feature_vec:
    df_sim_results = db.find_similar_history(current_feature_vec, str(selected_date), top_n=3)
    
    if not df_sim_results.empty:
        fig_sim = go.Figure()

        curr_path = db.get_kline_window(stock_code, str(selected_date), days_before=20, days_after=0)
        if not curr_path.empty:
            fig_sim.add_trace(go.Scatter(x=curr_path['day_offset'], y=curr_path['norm_close'], 
                                         name=f"分析标的: {stock_code}", line=dict(color='#000000', width=3)))

        path_colors = ['#c62828', '#1565c0', '#ef6c00']
        for i, row in df_sim_results.iterrows():
            hist_path = db.get_kline_window(row['stock_code'], str(row['trade_date']), days_before=20, days_after=20)
            if not hist_path.empty:
                fig_sim.add_trace(go.Scatter(x=hist_path['day_offset'], y=hist_path['norm_close'], 
                                             name=f"相似样本{i+1}: {row['stock_name']} ({row['trade_date']})",
                                             line=dict(color=path_colors[i % 3], dash='dot'), opacity=0.7))
        
        fig_sim.add_vline(x=0, line_dash="dash", annotation_text="T+0 观测点")
        fig_sim.update_layout(title="形态相似度对标与后向预测参考", xaxis_title="相对交易日 (T+n)", 
                              yaxis_title="归一化价格系数 (Base=1.0)", height=500, template="plotly_white")
        st.plotly_chart(fig_sim, use_container_width=True)
        st.dataframe(df_sim_results, use_container_width=True, hide_index=True)
    else:
        st.warning("相似性检索失败：未在历史库中发现具有显著相关性的样本")
else:
    st.info("数据完整性提示：当前断面技术指标缺失，无法执行形态匹配算法")