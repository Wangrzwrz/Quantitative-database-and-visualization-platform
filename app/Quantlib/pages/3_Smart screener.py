import streamlit as st
import pandas as pd
from utils import get_db_connection

st.set_page_config(page_title="多因子选股器", layout="wide")
db = get_db_connection()

# 初始化全局交易日期状态
if 'global_date' not in st.session_state:
    st.session_state['global_date'] = db.get_latest_trade_date()

st.title("多因子量化选股")

# ================= 1. 样本周期配置 =================
with st.sidebar:
    st.header("观测参数设置")
    # 确定截面数据分析的基准日期
    picked_date = st.date_input("样本观测日", value=st.session_state['global_date'])
    if picked_date != st.session_state['global_date']:
        st.session_state['global_date'] = picked_date
        st.rerun()
    date_str = str(st.session_state['global_date'])

# ================= 2. 数据获取与预处理 =================
@st.cache_data(ttl=600)
def load_screener_data(d):
    """从数据库获取全市场截面因子数据"""
    return db.get_screener_data(d)

try:
    with st.spinner(f"正在调取 {date_str} 市场截面因子数据集..."):
        df = load_screener_data(date_str)
    
    if df.empty:
        st.error("系统提示：选定日期截面数据缺失。")
        st.stop()

    df.columns = [c.split('.')[-1] for c in df.columns]

    factor_columns = [
        'pct_chg', 'close', 'turnover_rate', 'total_mv_yi', 'pe_ttm', 'pb', 'roe_ttm', 
        'dividend_yield', 'yoy_profit', 'ma_5', 'ma_20', 'ma_60', 'rsi_14', 'bias_20',
        'month_mom', 'volatility', 'limit_up_streak', 'seal_money'
    ]
    for col in factor_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    if 'total_mv_yi' in df.columns:
        df = df[df['total_mv_yi'] > 10.0]

except Exception as e:
    st.error(f"数据加载异常: {e}")
    st.stop()

# ================= 3. 多因子过滤模型 =================
st.subheader("因子过滤条件配置")

# --- A. 基本面因子 ---
with st.expander("基本面评估 (市值 / 估值 / 盈利能力)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    
    max_mv_observed = int(df['total_mv_yi'].max()) if 'total_mv_yi' in df.columns else 5000
    mv_min, mv_max = c1.slider("总市值区间 (亿元)", 10, max_mv_observed, (50, min(5000, max_mv_observed)), step=10)
    pe_range = c2.slider("市盈率 PE (TTM) 区间", 0, 200, (0, 80))
    roe_min = c3.number_input("净资产收益率 ROE (TTM) > (%)", value=0.0, step=1.0)
    yoy_min = c4.number_input("归母净利润增长率 (YoY) > (%)", value=-100.0, step=10.0)

# --- B. 技术面因子 ---
with st.expander("技术指标与趋势动量", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    pct_range = c1.slider("截面收益率范围 (%)", -20.0, 20.0, (-5.0, 10.0))
    turn_min = c2.number_input("单日换手率下限 (%)", value=0.0, step=1.0)
    rsi_min = c3.number_input("RSI (14) 指标下限", value=0)
    ma_alignment = c4.checkbox("均线多头排列特征 (MA5 > MA20 > MA60)", value=False)

# --- C. 动量与波动率 ---
with st.expander("价格动量与风险波动", expanded=False):
    c1, c2 = st.columns(2)
    mom_min = c1.number_input("中期动量 (20日累计收益率%) >", value=-20.0, step=5.0)
    vol_max = c2.number_input("20日年化波动率上限 <", value=100.0, step=5.0)

# --- D. 情绪因子与极端波动 ---
with st.expander("市场情绪与流动性溢价", expanded=False):
    c1, c2, c3 = st.columns(3)
    streak_min = c1.number_input("最低连板高度 (Streak)", value=0, min_value=0)
    seal_min_wan = c2.number_input("封单金额下限 (万)", value=0, step=100)
    only_zt = c3.checkbox("仅筛选价格涨停样本", value=False)

# ================= 4. 筛选逻辑执行 =================
try:
    f_df = df.copy()
    
    # 执行基本面过滤逻辑
    if 'total_mv_yi' in f_df.columns:
        f_df = f_df[(f_df['total_mv_yi'] >= mv_min) & (f_df['total_mv_yi'] <= mv_max)]
    if 'pe_ttm' in f_df.columns:
        f_df = f_df[(f_df['pe_ttm'] >= pe_range[0]) & (f_df['pe_ttm'] <= pe_range[1])]
    if 'roe_ttm' in f_df.columns:
        f_df = f_df[f_df['roe_ttm'] >= roe_min]
    if 'yoy_profit' in f_df.columns:
        f_df = f_df[f_df['yoy_profit'] >= yoy_min]
    
    # 执行技术面过滤逻辑
    if 'pct_chg' in f_df.columns:
        f_df = f_df[(f_df['pct_chg'] >= pct_range[0]) & (f_df['pct_chg'] <= pct_range[1])]
    if 'turnover_rate' in f_df.columns:
        f_df = f_df[f_df['turnover_rate'] >= turn_min]
    if 'rsi_14' in f_df.columns:
        f_df = f_df[f_df['rsi_14'] >= rsi_min]
    if ma_alignment and 'ma_5' in f_df.columns:
        f_df = f_df[(f_df['ma_5'] > f_df['ma_20']) & (f_df['ma_20'] > f_df['ma_60'])]
        
    # 执行动量与波动率过滤
    if 'month_mom' in f_df.columns:
        f_df = f_df[f_df['month_mom'] >= mom_min]
    if 'volatility' in f_df.columns:
        f_df = f_df[f_df['volatility'] <= vol_max]
    
    # 执行情绪因子过滤
    if 'limit_up_streak' in f_df.columns:
        f_df = f_df[f_df['limit_up_streak'] >= streak_min]
    if seal_min_wan > 0 and 'seal_money' in f_df.columns:
        f_df = f_df[f_df['seal_money'] >= seal_min_wan * 10000]
    if only_zt and 'is_limit_up' in f_df.columns:
        f_df = f_df[f_df['is_limit_up'] == 1]

except Exception as e:
    st.error(f"逻辑执行引擎错误: {e}")
    st.stop()

# ================= 5. 筛选结果呈现 =================
st.divider()
c_res, c_act = st.columns([8, 2])

with c_res:
    st.subheader(f"样本池筛选结果: {len(f_df)} 标的")
    
    if not f_df.empty:
        sorting_dimension = {
            '收益率': 'pct_chg', '动量效应': 'month_mom', 
            '估值水平': 'pe_ttm', '资产规模': 'total_mv_yi', '连板高度': 'limit_up_streak'
        }
        c_sort, c_asc = st.columns([3, 1])
        sort_key = c_sort.selectbox("因子排序依据 (Primary Sort)", list(sorting_dimension.keys()), index=0)
        is_ascending = c_asc.checkbox("升序排列", value=False)
        
        target_col = sorting_dimension[sort_key]
        display_df = f_df.sort_values(target_col, ascending=is_ascending).reset_index(drop=True)

        reporting_cols = [
            'stock_code', 'stock_name', 'industry', 'pct_chg', 'close', 
            'total_mv_yi', 'pe_ttm', 'month_mom', 'limit_up_streak', 'roe_ttm'
        ]
        final_reporting_set = [c for c in reporting_cols if c in display_df.columns]
        
        st.dataframe(
            display_df[final_reporting_set],
            column_config={
                "stock_code": "代码", "stock_name": "简称", "industry": "所属申万行业",
                "pct_chg": st.column_config.NumberColumn("单日收益率", format="%.2f%%"),
                "close": st.column_config.NumberColumn("收盘价", format="%.2f"),
                "total_mv_yi": st.column_config.NumberColumn("总市值(亿)", format="%.1f"),
                "pe_ttm": st.column_config.NumberColumn("市盈率(TTM)", format="%.1f"),
                "month_mom": st.column_config.NumberColumn("月动量", format="%.1f%%"),
                "limit_up_streak": st.column_config.NumberColumn("连板天数", format="%d"),
                "roe_ttm": st.column_config.NumberColumn("ROE(%)", format="%.1f")
            },
            use_container_width=True,
            height=600
        )
    else:
        st.info("提示：当前因子组合条件下无匹配样本，建议调整过滤阈值。")

with c_act:
    st.subheader("个体深度研判")
    if not f_df.empty:
        top_samples = f_df.head(15)
        for _, row in top_samples.iterrows():
            if st.button(f"穿透分析: {row['stock_name']}", key=f"scr_{row['stock_code']}", use_container_width=True):
                st.session_state['selected_stock'] = row['stock_code']
                st.switch_page("pages/4_Stock deepdive.py")
        
        if len(f_df) > 15:
            st.caption(f"注：仅展示首选 15 只样本。")