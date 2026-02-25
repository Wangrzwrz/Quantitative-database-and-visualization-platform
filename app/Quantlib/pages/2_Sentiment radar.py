import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_db_connection

st.set_page_config(page_title="市场情绪监控", layout="wide")
db = get_db_connection()

# ================= 1. 全局状态与控制面板 =================
if 'global_date' not in st.session_state:
    st.session_state['global_date'] = db.get_latest_trade_date()

with st.sidebar:
    st.header("交易配置中心")

    picked_date = st.date_input("分析基准日", value=st.session_state['global_date'])
    if picked_date != st.session_state['global_date']:
        st.session_state['global_date'] = picked_date
        st.rerun()
    
    date_str = str(st.session_state['global_date'])
    prev_date = db.get_previous_trading_date(date_str)
    if not prev_date: 
        prev_date = st.session_state['global_date']

    compare_date = st.date_input("对比基准日", prev_date)
    comp_date_str = str(compare_date)

st.title("市场情绪量化")

# ================= 2. 数据获取与预处理 =================
try:
    df_stats = db.get_daily_limit_stats(date_str)
    df_stats_comp = db.get_daily_limit_stats(comp_date_str)
    df_ladder = db.get_kpl_ladder(date_str)
    df_down_detail = db.get_limit_down_detail(date_str)
    df_snap = db.get_market_snapshot(date_str)
    df_snap_comp = db.get_market_snapshot(comp_date_str)
    df_trend = db.get_sentiment_trend(days=30)
    df_broken = db.get_limit_broken_detail(date_str)
    zt_premium, _ = db.get_yesterday_limit_up_performance(date_str, str(prev_date))
    df_factors = db.get_sentiment_factor_rank(date_str)
    
    def safe_numeric(df, cols):
        """类型强制转换工具：确保分析维度为数值型"""
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    df_snap = safe_numeric(df_snap, ['pct_chg', 'amount'])
    df_broken = safe_numeric(df_broken, ['pct_chg', 'turnover_rate'])
    
    def clean_sentiment_data(df):
        """情绪专题数据标准化：处理封单金额单位及连板高度"""
        if df.empty: return df
        
        def parse_monetary_value(x):
            try:
                x_str = str(x)
                if '亿' in x_str: return float(x_str.replace('亿','')) * 1e8
                if '万' in x_str: return float(x_str.replace('万','')) * 1e4
                return float(x)
            except: return 0.0

        if df['seal_amt'].dtype == 'object':
            df['seal_val'] = df['seal_amt'].apply(parse_monetary_value)
        else:
            df['seal_val'] = pd.to_numeric(df['seal_amt'], errors='coerce').fillna(0)
            
        df['seal_show'] = df['seal_val'].apply(lambda x: f"{x/1e8:.2f}亿" if x > 1e8 else f"{x/1e4:.0f}万")

        if 'reason' in df.columns:
            df['reason'] = df['reason'].replace('', '未分类').fillna('未分类')
        if 'limit_time' in df.columns:
            df['limit_time'] = df['limit_time'].replace('', '--:--').fillna('--:--')

        if 'height' not in df.columns and 'streak' in df.columns:
            extracted = df['streak'].astype(str).str.extract(r'(\d+)')
            df['height'] = extracted.astype(float).fillna(1).astype(int)
        
        return df

    df_ladder = clean_sentiment_data(df_ladder)
    df_down_detail = clean_sentiment_data(df_down_detail)

except Exception as e:
    st.error(f"数据处理引擎异常: {e}")
    st.stop()

# ================= 3. 核心风险偏好指标 =================
st.subheader("市场情绪检测")
k1, k2, k3, k4, k5, k6 = st.columns(6)

if not df_snap.empty:
    amt_now = df_snap['amount'].sum()
    amt_comp = df_snap_comp['amount'].sum() if not df_snap_comp.empty else amt_now
    diff = amt_now - amt_comp
    k1.metric("成交总量", f"{amt_now/1e8:.0f}亿", f"{'+' if diff>0 else ''}{diff/1e8:.0f}亿", delta_color="off")

if not df_snap.empty:
    up_nodes = (df_snap['pct_chg'] > 0).sum()
    down_nodes = (df_snap['pct_chg'] < 0).sum()
    k2.metric("涨跌节点比", f"{up_nodes}:{down_nodes}", f"净增量 {up_nodes-down_nodes}", delta_color="normal")

limit_up_count = int(df_stats.iloc[0]['limit_up_count'])
limit_up_comp = int(df_stats_comp.iloc[0]['limit_up_count'])
k3.metric("涨停效应", f"{limit_up_count}", f"{limit_up_count - limit_up_comp} (DoD)", delta_color="normal")

broken_count = int(df_stats.iloc[0]['broken_count'])
broken_ratio = broken_count / (limit_up_count + broken_count) * 100 if (limit_up_count + broken_count) > 0 else 0
k4.metric("炸板率", f"{broken_ratio:.1f}%", f"样本数 {broken_count}", delta_color="inverse")

limit_down_count = int(df_stats.iloc[0]['limit_down_count'])
k5.metric("跌停效应", f"{limit_down_count}", "极端负反馈", delta_color="inverse")

k6.metric("隔日风险溢价", f"{zt_premium:.2f}%", "溢价一致性", delta_color="normal" if zt_premium > 0 else "inverse")

st.divider()

# ================= 4. 极端价格波动 =================
c_list_up, c_list_down = st.columns([1, 1])

with c_list_up:
    with st.expander("完整涨停列表 (封单降序)", expanded=True):
        if not df_ladder.empty:
            display_df = df_ladder[['limit_time', 'stock_name', 'height', 'reason', 'seal_show', 'seal_val']].copy()
            display_df = display_df.sort_values('seal_val', ascending=False)
            st.dataframe(
                display_df,
                column_config={"stock_name": "名称", "height": st.column_config.NumberColumn("连板数", format="%d"), "seal_show": "封单金额"},
                hide_index=True, use_container_width=True, height=300
            )
        else:
            st.info("当前断面无涨停样本")

with c_list_down:
    with st.expander("完整跌停列表 (封单降序)", expanded=True):
        if not df_down_detail.empty:
            display_down = df_down_detail[['limit_time', 'stock_name', 'reason', 'seal_show', 'seal_val']].copy()
            display_down = display_down.sort_values('seal_val', ascending=False)
            st.dataframe(
                display_down,
                column_config={"stock_name": "名称", "reason": "逻辑归因", "seal_show": "封单金额"},
                hide_index=True, use_container_width=True, height=300
            )
        else:
            st.success("市场暂无跌停反馈")

st.divider()

# ================= 5. 题材热力与资金流向 =================
st.subheader("题材板块深度分析")

plate_stats = pd.DataFrame()
if not df_ladder.empty:
    plate_stats = df_ladder.groupby('plate').agg(
        count=('stock_code', 'count'),
        total_money=('seal_val', 'sum'),
        max_height=('height', 'max')
    ).reset_index().sort_values('total_money', ascending=False)
    plate_stats['money_display'] = (plate_stats['total_money']/1e8).apply(lambda x: f"{x:.2f}亿")

c_tree, c_list = st.columns([7, 3])

with c_tree:
    if not plate_stats.empty:
        fig_tree = px.treemap(
            plate_stats, path=['plate'], values='total_money', color='count',
            color_continuous_scale='Reds', 
            title="资金攻击向量分布",
            custom_data=['count', 'max_height', 'money_display']
        )
        fig_tree.update_traces(hovertemplate='<b>行业板块: %{label}</b><br>涨停家数: %{customdata[0]}<br>最高连板: %{customdata[1]}<br>总封单额: %{customdata[2]}')
        fig_tree.update_layout(margin=dict(t=30, l=0, r=0, b=0), height=500)
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("板块动量数据缺失")

with c_list:
    st.markdown("**板块资金排名**")
    if not plate_stats.empty:
        st.dataframe(
            plate_stats[['plate', 'money_display', 'count']],
            column_config={
                "plate": "行业板块", "money_display": "累计封单额", "count": st.column_config.NumberColumn("样本量", format="%d")
            },
            hide_index=True, height=500, use_container_width=True
        )

if not plate_stats.empty:
    all_plates = plate_stats['plate'].tolist()
    c_sel, c_blank = st.columns([1, 2])
    with c_sel:
        target_plate = st.selectbox("细分题材穿透分析:", all_plates, index=0)
    
    if target_plate:
        subset = df_ladder[df_ladder['plate'] == target_plate].copy()
        subset = subset.sort_values(['height', 'seal_val'], ascending=[False, False])
        st.dataframe(
            subset[['stock_name', 'stock_code', 'height', 'seal_show', 'reason', 'limit_time']],
            column_config={
                "stock_name": "证券名称", "stock_code": "证券代码",
                "height": st.column_config.NumberColumn("连板高度", format="%d"),
                "seal_show": "封单规模", "reason": "驱动逻辑", "limit_time": "首次触板"
            },
            hide_index=True, use_container_width=True
        )

st.divider()

# ================= 6. 情绪周期序列 =================
st.subheader("情绪周期历史趋势分析")
if not df_trend.empty:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_trend['limit_up'] = pd.to_numeric(df_trend['limit_up'], errors='coerce').fillna(0)
    df_trend['limit_down'] = pd.to_numeric(df_trend['limit_down'], errors='coerce').fillna(0)
    
    fig.add_trace(go.Bar(x=df_trend['trade_date'], y=df_trend['limit_up'], name="涨停效应", marker_color='#c62828'), secondary_y=False)
    fig.add_trace(go.Bar(x=df_trend['trade_date'], y=-df_trend['limit_down'], name="跌停效应", marker_color='#2e7d32'), secondary_y=False)
    fig.update_layout(height=400, margin=dict(t=30, b=0, l=0, r=0), showlegend=True, title_text="多空动量净值演变序列")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ================= 7. 涨/跌停阶梯分析 =================
st.subheader("涨停梯队")

if not df_ladder.empty:
    unique_heights = sorted(df_ladder['height'].unique(), reverse=True)
    COLS_PER_ROW = 5 
    for i in range(0, len(unique_heights), COLS_PER_ROW):
        row_heights = unique_heights[i : i + COLS_PER_ROW]
        cols = st.columns(len(row_heights))
        for idx, height in enumerate(row_heights):
            with cols[idx]:
                current_group = df_ladder[df_ladder['height'] == height].sort_values('limit_time')
                label = f"{height} 连板 (样本量: {len(current_group)})"
                with st.expander(label, expanded=False):
                    for _, row in current_group.iterrows():
                        c = st.container(border=True)
                        c.caption(f"{row['limit_time']} | {row['stock_code']}")
                        c.markdown(f"**{row['stock_name']}**")
                        c.text(f"封单: {row['seal_show']}")
                        reason_disp = str(row['reason'])
                        c.caption(f"逻辑: {reason_disp[:12]}..." if len(reason_disp) > 12 else f"逻辑: {reason_disp}")
                        
                        if c.button("穿透研究", key=f"up_{row['stock_code']}"):
                            st.session_state['selected_stock'] = row['stock_code']
                            st.switch_page("pages/4_Stock deepdive.py")
else:
    st.info("交易日无涨停梯队样本")

st.subheader("跌停梯队")
if not df_down_detail.empty:
    unique_heights_down = sorted(df_down_detail['height'].unique(), reverse=True)
    if len(unique_heights_down) == 0: unique_heights_down = [1]

    for i in range(0, len(unique_heights_down), COLS_PER_ROW):
        row_heights = unique_heights_down[i : i + COLS_PER_ROW]
        cols = st.columns(len(row_heights))
        for idx, height in enumerate(row_heights):
            with cols[idx]:
                current_group = df_down_detail[df_down_detail['height'] == height]
                label = f"跌停 {height} 级 (样本量: {len(current_group)})"
                with st.expander(label, expanded=False):
                    for _, row in current_group.iterrows():
                        c = st.container(border=True)
                        c.markdown(f"**{row['stock_name']}**")
                        c.caption(f"风险封单: {row['seal_show']}")
                        if c.button("穿透研究", key=f"down_{row['stock_code']}"):
                            st.session_state['selected_stock'] = row['stock_code']
                            st.switch_page("pages/4_Stock deepdive.py")
else:
    st.success("今日无连板跌停")

st.divider()

# ================= 8. 主力封单排行 =================
st.subheader("主力封单排行")

if not df_ladder.empty:
    with st.expander("封单金额排序", expanded=False):
        all_seal = df_ladder.sort_values('seal_val', ascending=False)
        st.dataframe(
            all_seal[['stock_name', 'seal_show', 'reason', 'height', 'limit_time']],
            column_config={
                "stock_name": "名称", "seal_show": "封单金额",
                "height": st.column_config.NumberColumn("板数", format="%d板"),
                "limit_time": "时间"
            },
            hide_index=True, height=600, use_container_width=True
        )
else: st.info("暂无数据")

st.divider()

# ================= 9. 炸板观测池 =================
st.subheader("非持续性涨停（炸板）样本库")
st.caption("当日曾触及涨停价格但未能维持至收盘的标的，反映盘中承接意愿与阻力。")

if not df_broken.empty:
    with st.expander("全量炸板明细数据", expanded=False):
        st.dataframe(
            df_broken[['stock_name', 'first_limit_time', 'pct_chg', 'turnover_rate', 'reason']],
            column_config={
                "pct_chg": st.column_config.NumberColumn("收盘收益率", format="%.2f%%"),
                "turnover_rate": st.column_config.NumberColumn("换手率", format="%.2f%%")
            },
            hide_index=True, use_container_width=True
        )
        
    strong_broken = df_broken[df_broken['pct_chg'] > 5].sort_values('pct_chg', ascending=False)
    label_strong = f"强承接样本精选 (收盘涨幅 > 5%, 样本数: {len(strong_broken)})"
    
    with st.expander(label_strong, expanded=False):
        if not strong_broken.empty:
            cols = st.columns(6)
            for i, row in enumerate(strong_broken.itertuples()):
                with cols[i % 6]:
                    c = st.container(border=True)
                    c.markdown(f"**{row.stock_name}**")
                    c.caption(f"收盘涨幅: +{row.pct_chg:.2f}%")
                    if c.button("分析", key=f"brk_{row.stock_code}"):
                        st.session_state['selected_stock'] = row.stock_code
                        st.switch_page("pages/4_Stock deepdive.py")
        else:
            st.info("今日无高承接位炸板样本")
else:
    st.info("当前断面无炸板观测数据")

st.divider()

# ================= 10. 情绪因子截面数据 =================
st.subheader("情绪因子截面分布")
if not df_factors.empty:
    has_money_data = df_factors['money_flow_main'].notnull().any()
    if has_money_data:
        st.markdown("**主力资金净流入分布 (Top 20)**")
        st.bar_chart(df_factors.set_index('stock_name')['money_flow_main'].head(20))
    else:
        st.info("主力净流入数据缺省，以下展示封单因子快照：")
        st.dataframe(
            df_factors[['stock_code', 'stock_name', 'limit_up_streak', 'kpl_seal_money']].head(10),
            column_config={"kpl_seal_money": st.column_config.NumberColumn("封单金额因子", format="¥%.0f")},
            hide_index=True, use_container_width=True
        )
else:
    st.info("数据异常：因子数据库无法提供当前断面数据")