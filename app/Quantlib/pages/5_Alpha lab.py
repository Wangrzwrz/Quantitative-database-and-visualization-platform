import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import spearmanr
from utils import get_db_connection

st.set_page_config(page_title="Alpha 因子看板", layout="wide")
db = get_db_connection()

if 'global_date' not in st.session_state:
    st.session_state['global_date'] = db.get_latest_trade_date()

st.title("Alpha 因子工作台)")
st.caption("集成因子截面扫描、时序稳定性分析与资产穿透研判的量化分析平台。")

# ================= 1. 控制面板 =================
with st.sidebar:
    st.header("控制参数")
    picked_date = st.date_input("样本观测日", value=st.session_state['global_date'])
    if picked_date != st.session_state['global_date']:
        st.session_state['global_date'] = picked_date
        st.rerun()
    date_str = str(st.session_state['global_date'])

    if 'all_alphas' not in st.session_state:
        st.session_state['all_alphas'] = db.get_all_alpha_names()

tab_kanban, tab_deep = st.tabs(["因子截面扫描", "单因子深度分析"])

# ================= 2. 因子全景扫描 =================
with tab_kanban:
    st.subheader(f"{date_str} 全市场因子截面有效性扫描")
    
    col_k1, col_k2 = st.columns([1, 4])
    with col_k1:
        st.markdown("**执行全量计算**")
        st.caption("扫描 101 个特征因子的截面秩相关系数 (Rank IC)。")
        run_scan = st.button("开始全量扫描", type="primary")
    
    if run_scan:
        with st.spinner("正在提取截面数据并执行 Spearman 秩相关计算..."):
            df_wide = db.get_cross_section_all_alphas(date_str)

            df_wide.columns = [c.split('.')[-1] for c in df_wide.columns]
            
            if not df_wide.empty and 'pct_chg' in df_wide.columns:
                alpha_cols = [c for c in df_wide.columns if c.startswith('alpha_')]

                ic_series = df_wide[alpha_cols].corrwith(df_wide['pct_chg'], method='spearman')
                
                df_ic = ic_series.to_frame(name='Rank_IC').reset_index().rename(columns={'index': 'Factor'})
                df_ic['Abs_IC'] = df_ic['Rank_IC'].abs()
                df_ic = df_ic.sort_values('Abs_IC', ascending=False).reset_index(drop=True)
                
                with col_k2:
                    top_pos = df_ic.sort_values('Rank_IC', ascending=False).head(10)
                    top_neg = df_ic.sort_values('Rank_IC', ascending=True).head(10)
                    
                    fig_ic = go.Figure()
                    fig_ic.add_trace(go.Bar(
                        x=top_pos['Factor'], y=top_pos['Rank_IC'],
                        name='正向有效', marker_color='#c62828'
                    ))
                    fig_ic.add_trace(go.Bar(
                        x=top_neg['Factor'], y=top_neg['Rank_IC'],
                        name='负向有效', marker_color='#2e7d32'
                    ))
                    fig_ic.update_layout(title="今日因子截面 IC 分布 (Top 10 Leaders/Laggards)", height=400, template="plotly_white")
                    st.plotly_chart(fig_ic, use_container_width=True)
                
                st.subheader("因子相关性详细数据集")
                st.dataframe(
                    df_ic[['Factor', 'Rank_IC']],
                    column_config={
                        "Factor": "因子代码",
                        "Rank_IC": st.column_config.NumberColumn("Rank IC (秩相关)", format="%.4f")
                    },
                    use_container_width=True, height=300
                )
            else:
                st.error("计算终止：数据源中缺失段。")
    else:
        with col_k2:
            st.info("系统就绪：请下达扫描指令。")

# ================= 3. 单因子纵向研判 =================
with tab_deep:
    c_sel, c_blank = st.columns([1, 3])
    with c_sel:
        target_alpha = st.selectbox("分析目标因子", st.session_state['all_alphas'], index=0)
    
    st.divider()

    with st.spinner(f"正在构建 {target_alpha} 历史绩效序列..."):
        df_hist = db.get_single_alpha_history(target_alpha, date_str, days=60)
    
    if not df_hist.empty:
        df_hist.columns = [c.split('.')[-1] for c in df_hist.columns]
        
        st.subheader(f"因子稳定性与单调性分析 (Performance Analysis: {target_alpha})")

        daily_ic = df_hist.groupby('trade_date').apply(
            lambda x: spearmanr(x['alpha_val'], x['pct_chg'])[0]
        ).reset_index(name='Daily_IC')
        
        daily_ic['Cumulative_IC'] = daily_ic['Daily_IC'].cumsum()
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            fig_ic_ts = px.bar(daily_ic, x='trade_date', y='Daily_IC', title="因子单日 IC 时序分布")
            fig_ic_ts.update_traces(marker_color=np.where(daily_ic['Daily_IC']<0, '#2e7d32', '#c62828'))
            fig_ic_ts.update_layout(template="plotly_white")
            st.plotly_chart(fig_ic_ts, use_container_width=True)
            
        with c_chart2:
            fig_cum = px.line(daily_ic, x='trade_date', y='Cumulative_IC', title="累积 IC 曲线 (因子预测稳定性)")
            fig_cum.update_traces(line_color='#1565c0', line_width=2.5)
            fig_cum.update_layout(template="plotly_white")
            st.plotly_chart(fig_cum, use_container_width=True)

        st.subheader("因子单日分层收益分析")
        
        df_today = df_hist[df_hist['trade_date'].dt.strftime('%Y-%m-%d') == date_str].copy()
        
        if not df_today.empty:
            try:
                df_today['group'] = pd.qcut(df_today['alpha_val'], 10, labels=False, duplicates='drop')
                group_ret = df_today.groupby('group')['pct_chg'].mean().reset_index()
                
                fig_layer = px.bar(
                    group_ret, x='group', y='pct_chg',
                    title=f"{date_str} 分层平均收益率分布",
                    labels={'group': '因子分组 (0=最小值, 9=最大值)', 'pct_chg': '平均收益率 (%)'}
                )
                fig_layer.update_traces(marker_color=np.where(group_ret['pct_chg']<0, '#2e7d32', '#c62828'))
                fig_layer.update_layout(template="plotly_white")
                st.plotly_chart(fig_layer, use_container_width=True)
            except Exception:
                st.warning("因子暴露值分布过于集中，无法进行分层分位数分析。")
        else:
            st.info("目标观测日数据缺失。")

        st.divider()
        st.subheader("因子暴露度极端样本分析")
        
        df_list = db.get_alpha_top_bottom_list(date_str, target_alpha)
        
        if not df_list.empty:
            df_list.columns = [c.split('.')[-1] for c in df_list.columns]
            
            c_top, c_bot = st.columns(2)
            col_config = {
                "stock_code": "证券代码", "stock_name": "证券简称", "industry": "所属行业",
                "alpha_val": st.column_config.NumberColumn("因子暴露值", format="%.4f"),
                "pct_chg": st.column_config.NumberColumn("日收益率", format="%.2f%%"),
                "close": st.column_config.NumberColumn("收盘价", format="%.2f")
            }
            
            with c_top:
                st.markdown(f"**最高暴露样本 (Factor Overweight Top 20)**")
                top_df = df_list.head(20).reset_index(drop=True)
                
                event_top = st.dataframe(
                    top_df[['stock_code', 'stock_name', 'industry', 'alpha_val', 'pct_chg', 'close']],
                    column_config=col_config, hide_index=True, use_container_width=True,
                    selection_mode="single-row", on_select="rerun", key="tbl_top"
                )
                
                if event_top.selection.rows:
                    idx = event_top.selection.rows[0]
                    st.session_state['selected_stock'] = top_df.iloc[idx]['stock_code']
                    st.switch_page("pages/4_Stock deepdive.py")

            with c_bot:
                st.markdown(f"**最低暴露样本 (Factor Underweight Bottom 20)**")
                bot_df = df_list.tail(20).sort_values('alpha_val', ascending=True).reset_index(drop=True)
                
                event_bot = st.dataframe(
                    bot_df[['stock_code', 'stock_name', 'industry', 'alpha_val', 'pct_chg', 'close']],
                    column_config=col_config, hide_index=True, use_container_width=True,
                    selection_mode="single-row", on_select="rerun", key="tbl_bot"
                )
                
                if event_bot.selection.rows:
                    idx = event_bot.selection.rows[0]
                    st.session_state['selected_stock'] = bot_df.iloc[idx]['stock_code']
                    st.switch_page("pages/4_Stock deepdive.py")
        else:
            st.warning("底层资产暴露度明细无法调取。")
    else:
        st.warning("该因子的历史样本容量不足以支持纵向回溯分析。")