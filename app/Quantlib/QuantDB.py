import clickhouse_connect
import pandas as pd
from datetime import datetime, timedelta

class QuantDB:
    """量化平台核心数据库交互类"""

    def __init__(self, host='', port='', user='', password='', database=''):
        """初始化 ClickHouse 客户端连接"""
        self.client = clickhouse_connect.get_client(
            host=host, 
            port=port, 
            username=user, 
            password=password, 
            database=database
        )

    def _fix_code(self, code):
        """标准化证券代码格式"""
        if not code: 
            return '000001.SH'
        code = str(code).strip().upper()
        if code.endswith(('.SZ', '.SH', '.BJ')): 
            return code
        return f"{code}.SH" if code.startswith('6') else f"{code}.SZ"

    def get_latest_trade_date(self):
        """获取全库最新有效交易日期"""
        sql = "SELECT max(trade_date) FROM market_stock_active_daily"
        try:
            res = self.client.query(sql).result_rows
            return res[0][0] if res else datetime.now().date()
        except Exception:
            return datetime.now().date()

    def get_previous_trading_date(self, date_str):
        """查询指定日期的前一个有效交易日"""
        sql = f"SELECT max(trade_date) FROM market_stock_active_daily WHERE trade_date < '{date_str}'"
        try:
            res = self.client.query(sql).result_rows
            return res[0][0] if (res and res[0][0]) else None
        except Exception:
            return None

    def get_stock_info(self, code):
        """查询个股基础属性：名称、行业、地域及上市时间"""
        code = self._fix_code(code)
        sql = f"SELECT name, industry, area, list_date FROM meta_stock_info WHERE ts_code = '{code}' LIMIT 1"
        try:
            df = self.client.query_df(sql)
            return df.iloc[0].to_dict() if not df.empty else {'name': code, 'industry': '-', 'area': '-'}
        except Exception:
            return {'name': code, 'industry': '-', 'area': '-'}

    def get_stock_available_range(self, stock_code):
        """查询特定个股在数据库中的日期覆盖范围"""
        code = self._fix_code(stock_code)
        sql = f"SELECT min(trade_date), max(trade_date) FROM market_stock_active_daily WHERE stock_code = '{code}'"
        try:
            res = self.client.query(sql).result_rows
            return res[0][0], res[0][1]
        except Exception:
            return None, None
    
    def get_stock_base_kline(self, stock_code, start_date, end_date):
        """获取指定时间范围的基础K线数据"""
        code = self._fix_code(stock_code)
        sql = f"""
            SELECT trade_date, open_qfq AS open, close_qfq AS close, high_qfq AS high, low_qfq AS low,
                   vol, pct_chg, turnover_rate
            FROM market_stock_active_daily
            WHERE stock_code = '{code}' AND trade_date >= '{start_date}' AND trade_date <= '{end_date}'
            ORDER BY trade_date
        """
        return self.client.query_df(sql)

    def get_stock_dynamic_indicators(self, stock_code, start_date, end_date, field_configs):
        """基于配置动态构建多表关联查询, 提取多维因子序列"""
        code = self._fix_code(stock_code)
        select_parts = ["t_base.trade_date AS trade_date"]
        joins = []
        for i, config in enumerate(field_configs):
            alias = f"t_{i}"
            db_name = config.get('db', 'factor_db')
            for col in config['cols']: 
                select_parts.append(f"{alias}.{col} AS {col}")
            joins.append(f"LEFT JOIN {db_name}.{config['table']} AS {alias} "
                         f"ON t_base.stock_code = {alias}.stock_code AND t_base.trade_date = {alias}.trade_date")

        sql = f"""
            SELECT {', '.join(select_parts)}
            FROM market_stock_active_daily AS t_base
            {' '.join(joins)}
            WHERE t_base.stock_code = '{code}' 
              AND t_base.trade_date >= '{start_date}' 
              AND t_base.trade_date <= '{end_date}'
            ORDER BY t_base.trade_date
        """
        return self.client.query_df(sql)

    def get_stock_factor_snapshot(self, stock_code, target_date):
        """提取个股在特定日期的因子全景快照（涵盖技术、基本面、情绪、动量）"""
        code = self._fix_code(stock_code)
        sql = f"""
            SELECT 
                t1.trade_date, t1.close_qfq AS close, t1.pct_chg, t1.turnover_rate, t1.amount,
                t3.pe_ttm, t3.pb, t3.total_mv, t3.dv_ratio AS dividend_yield,
                t6.pe_zscore_60 AS pe_zscore, t6.pb_zscore_60 AS pb_zscore, t6.roe_ttm, t6.yoy_net_profit AS yoy_profit,
                t5.roc_20, t5.volatility_20, t5.pos_20 AS price_pos_20, 
                t2.bias_20, t2.rsi_14, t2.kdj_j, t2.cci_14, t2.wr_14,
                t4.limit_up_streak, t4.kpl_seal_money, t4.is_limit_up, t4.is_limit_broken, t4.money_flow_main
            FROM market_stock_active_daily AS t1
            LEFT JOIN factor_db.factor_technical_daily AS t2 ON t1.stock_code = t2.stock_code AND t1.trade_date = t2.trade_date
            LEFT JOIN stock_fundamental_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            LEFT JOIN factor_db.factor_sentiment_daily AS t4 ON t1.stock_code = t4.stock_code AND t1.trade_date = t4.trade_date
            LEFT JOIN factor_db.factor_momentum_daily AS t5  ON t1.stock_code = t5.stock_code AND t1.trade_date = t5.trade_date
            LEFT JOIN factor_db.factor_value_daily AS t6    ON t1.stock_code = t6.stock_code AND t1.trade_date = t6.trade_date
            WHERE t1.stock_code = '{code}' AND t1.trade_date = '{target_date}'
            LIMIT 1
        """
        try:
            df = self.client.query_df(sql)
            return df.iloc[0].to_dict() if not df.empty else {}
        except Exception:
            return {}

    def get_stock_fundamentals_history(self, stock_code, start_date, end_date):
        """查询个股基本面历史财务指标及股本变更数据"""
        code = self._fix_code(stock_code)
        sql = f"""
            SELECT trade_date, pe_ttm, pb, ps_ttm, dv_ratio AS dividend_yield,
                   total_mv, circ_mv, turnover_rate, total_share, float_share
            FROM stock_fundamental_daily
            WHERE stock_code = '{code}' AND trade_date >= '{start_date}' AND trade_date <= '{end_date}'
            ORDER BY trade_date DESC
        """
        return self.client.query_df(sql)

    def get_industry_peers_snapshot(self, stock_code, date):
        """获取同行业（申万二级）中市值排名前列的对标个股快照数据"""
        code = self._fix_code(stock_code)
        sql = f"""
            SELECT t1.stock_code AS stock_code, t1.pct_chg AS pct_chg, t1.turnover_rate AS turnover_rate,
                   t2.name AS stock_name,
                   t3.total_mv/100000000 AS mv_yi, t3.pe_ttm AS pe_ttm, t3.pb AS pb, t3.dv_ratio AS dividend,
                   t4.roe_ttm AS roe_ttm, t4.yoy_net_profit AS yoy_net_profit, sec.sector_name AS sector_name
            FROM market_stock_active_daily AS t1
            INNER JOIN rel_stock_sector AS sec ON t1.stock_code = sec.stock_code
            LEFT JOIN meta_stock_info AS t2 ON t1.stock_code = t2.ts_code
            LEFT JOIN stock_fundamental_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            LEFT JOIN factor_db.factor_value_daily AS t4 ON t1.stock_code = t4.stock_code AND t1.trade_date = t4.trade_date
            WHERE t1.trade_date = '{date}' AND sec.sector_type = 'SW2'
              AND sec.sector_name = (SELECT sector_name FROM rel_stock_sector WHERE stock_code = '{code}' AND sector_type = 'SW2' LIMIT 1)
            ORDER BY t3.total_mv DESC LIMIT 7
        """
        return self.client.query_df(sql)

    def get_screener_data(self, date):
        """多表关联查询：提取选股器所需的全市场因子宽表快照"""
        sql = f"""
            SELECT 
                base.stock_code AS stock_code, meta.name AS stock_name, meta.industry AS industry,
                base.pct_chg, base.close, base.turnover_rate, base.vol, base.amount,
                funda.total_mv/10000 AS total_mv_yi, funda.pe_ttm, funda.pb,
                val.roe_ttm, val.dividend_yield, val.yoy_net_profit AS yoy_profit,
                tech.ma_5, tech.ma_20, tech.ma_60, tech.rsi_14, tech.bias_20,
                mom.roc_20 AS month_mom, mom.volatility_20 AS volatility,
                sent.limit_up_streak, sent.kpl_seal_money AS seal_money, sent.is_limit_up, sent.is_limit_broken
            FROM market_stock_active_daily AS base
            LEFT JOIN stock_fundamental_daily AS funda ON base.stock_code=funda.stock_code AND base.trade_date=funda.trade_date
            LEFT JOIN factor_db.factor_value_daily AS val ON base.stock_code=val.stock_code AND base.trade_date=val.trade_date
            LEFT JOIN factor_db.factor_momentum_daily AS mom ON base.stock_code=mom.stock_code AND base.trade_date=mom.trade_date
            LEFT JOIN factor_db.factor_technical_daily AS tech ON base.stock_code=tech.stock_code AND base.trade_date=tech.trade_date
            LEFT JOIN factor_db.factor_sentiment_daily AS sent ON base.stock_code=sent.stock_code AND base.trade_date=sent.trade_date
            LEFT JOIN meta_stock_info AS meta ON base.stock_code = meta.ts_code
            WHERE base.trade_date = '{date}' AND funda.total_mv > 0
            LIMIT 8000
        """
        return self.client.query_df(sql)

    def get_technical_vector(self, stock_code, date):
        """获取个股形态特征向量(基于 RSI, CCI, BIAS 指标)"""
        sql = f"SELECT rsi_14, cci_14, bias_20 FROM factor_db.factor_technical_daily WHERE stock_code = '{stock_code}' AND trade_date = '{date}'"
        try:
            res = self.client.query(sql).result_rows
            return res[0] if res else None
        except Exception:
            return None

    def find_similar_history(self, current_vector, current_date, top_n=3):
        """全库搜索：基于加权欧氏距离匹配历史形态最接近的个股样本"""
        tgt_rsi, tgt_cci, tgt_bias = current_vector
        sql = f"""
            SELECT t1.stock_code, t1.trade_date, t2.name AS stock_name,
                   sqrt(pow(t1.rsi_14 - {tgt_rsi}, 2) + pow((t1.bias_20 - {tgt_bias}) * 5, 2) + pow((t1.cci_14 - {tgt_cci}) * 0.5, 2)) AS dist
            FROM factor_db.factor_technical_daily AS t1
            LEFT JOIN meta_stock_info AS t2 ON t1.stock_code = t2.ts_code
            WHERE t1.trade_date < '{current_date}' 
              AND t1.rsi_14 IS NOT NULL AND t1.bias_20 IS NOT NULL
            ORDER BY dist ASC LIMIT {top_n}
        """
        return self.client.query_df(sql)

    def get_kline_window(self, stock_code, center_date, days_before=10, days_after=20):
        """提取特定日期前后的K线序列, 并进行基准日价格归一化处理"""
        start_date = (pd.to_datetime(center_date) - timedelta(days=days_before*2)).strftime("%Y-%m-%d")
        end_date = (pd.to_datetime(center_date) + timedelta(days=days_after*2)).strftime("%Y-%m-%d")
        
        sql = f"SELECT trade_date, close_qfq AS close, pct_chg FROM market_stock_active_daily WHERE stock_code = '{stock_code}' AND trade_date >= '{start_date}' AND trade_date <= '{end_date}' ORDER BY trade_date"
        df = self.client.query_df(sql)
        if df.empty: return df
        
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.tz_localize(None)
        center_dt = pd.to_datetime(center_date).tz_localize(None)
        
        try:
            idx = df[df['trade_date'] <= center_dt].index[-1]
            start_idx, end_idx = max(0, idx - days_before), min(len(df), idx + days_after + 1)
            df_slice = df.iloc[start_idx:end_idx].copy()
            df_slice['day_offset'] = range(start_idx - idx, end_idx - idx)
            df_slice['norm_close'] = df_slice['close'] / df.iloc[idx]['close']
            return df_slice
        except Exception:
            return pd.DataFrame()

    def get_all_alpha_names(self):
        """通过元数据检索获取因子库中所有 Alpha 因子名称"""
        try:
            df = self.client.query_df("DESCRIBE factor_db.factor_alphas_daily")
            alphas = df[df['name'].str.startswith('alpha_')]['name'].tolist()
            return sorted(alphas)
        except Exception:
            return [f"alpha_{i:03d}" for i in range(1, 102)] 

    def get_alpha_performance_data(self, date, alpha_name):
        """获取单日因子分布及其对应的股票收益表现数据"""
        safe_alpha = alpha_name.replace("'", "")
        sql = f"""
            SELECT t1.stock_code AS stock_code, t2.name AS stock_name, t2.industry AS industry,
                   t1.{safe_alpha} AS alpha_value, t3.pct_chg AS pct_chg, t3.close AS close, t3.amount AS amount
            FROM factor_db.factor_alphas_daily AS t1
            LEFT JOIN meta_stock_info AS t2 ON t1.stock_code = t2.ts_code
            LEFT JOIN market_stock_active_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            WHERE t1.trade_date = '{date}' AND t3.pct_chg IS NOT NULL AND t1.{safe_alpha} IS NOT NULL
        """
        return self.client.query_df(sql)

    def get_cross_section_all_alphas(self, date):
        """获取全市场 Alpha 因子的横截面数据"""
        try:
            df_desc = self.client.query_df("DESCRIBE factor_db.factor_alphas_daily")
            alpha_cols = df_desc[df_desc['name'].str.startswith('alpha_')]['name'].tolist()
            alpha_select = ", ".join([f"t1.{c} AS {c}" for c in alpha_cols])
        except Exception:
            return pd.DataFrame() 

        sql = f"""
            SELECT t1.stock_code AS stock_code, t2.pct_chg AS pct_chg, {alpha_select}
            FROM factor_db.factor_alphas_daily AS t1
            LEFT JOIN market_stock_active_daily AS t2 ON t1.stock_code = t2.stock_code AND t1.trade_date = t2.trade_date
            WHERE t1.trade_date = '{date}' AND t2.pct_chg IS NOT NULL
        """
        return self.client.query_df(sql)

    def get_single_alpha_history(self, alpha_name, end_date, days=60):
        """获取特定因子在指定时间范围内的历史数值序列"""
        safe_alpha = alpha_name.replace("'", "")
        start_date = (pd.to_datetime(end_date) - timedelta(days=days*1.5)).strftime("%Y-%m-%d")
        sql = f"""
            SELECT t1.trade_date AS trade_date, t1.{safe_alpha} AS alpha_val, t2.pct_chg AS pct_chg
            FROM factor_db.factor_alphas_daily AS t1
            INNER JOIN market_stock_active_daily AS t2 ON t1.stock_code = t2.stock_code AND t1.trade_date = t2.trade_date
            WHERE t1.trade_date >= '{start_date}' AND t1.trade_date <= '{end_date}'
              AND t2.pct_chg IS NOT NULL AND t1.{safe_alpha} IS NOT NULL
            ORDER BY t1.trade_date
        """
        return self.client.query_df(sql)

    def get_alpha_top_bottom_list(self, date, alpha_name, top_n=20):
        """查询当日因子值最高及最低的个股榜单"""
        safe_alpha = alpha_name.replace("'", "")
        sql = f"""
            SELECT t1.stock_code AS stock_code, t3.name AS stock_name, t3.industry AS industry,
                   t1.{safe_alpha} AS alpha_val, t2.pct_chg AS pct_chg, t2.close AS close
            FROM factor_db.factor_alphas_daily AS t1
            LEFT JOIN market_stock_active_daily AS t2 ON t1.stock_code=t2.stock_code AND t1.trade_date=t2.trade_date
            LEFT JOIN meta_stock_info AS t3 ON t1.stock_code=t3.ts_code
            WHERE t1.trade_date = '{date}' AND t1.{safe_alpha} IS NOT NULL
            ORDER BY t1.{safe_alpha} DESC
        """
        return self.client.query_df(sql)

    def get_sector_rotation_rank(self, date):
        """统计申万二级行业的核心财务、行情及动量指标排名"""
        sql = f"""
            SELECT sec.sector_name AS sector_name, count(t1.stock_code) AS stock_count,
                   sum(t3.total_mv)/100000000 AS total_mv_yi, sum(t1.amount)/100000000 AS total_amt_yi,
                   avg(t1.pct_chg) AS avg_pct_chg, median(t3.pe_ttm) AS median_pe,
                   median(t3.pb) AS median_pb, avg(t5.roc_20) AS avg_mom_20,
                   avg(t1.turnover_rate) AS avg_turnover, avg(t2.rsi_14) AS avg_rsi
            FROM market_stock_active_daily AS t1
            INNER JOIN rel_stock_sector AS sec ON t1.stock_code = sec.stock_code
            LEFT JOIN factor_db.factor_technical_daily AS t2 ON t1.stock_code = t2.stock_code AND t1.trade_date = t2.trade_date
            LEFT JOIN stock_fundamental_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            LEFT JOIN factor_db.factor_momentum_daily AS t5 ON t1.stock_code = t5.stock_code AND t1.trade_date = t5.trade_date
            WHERE t1.trade_date = '{date}' AND sec.sector_type = 'SW2'
            GROUP BY sec.sector_name HAVING stock_count > 3
            ORDER BY total_amt_yi DESC
        """
        return self.client.query_df(sql)

    def get_sector_index_history(self, sector_name, end_date_str, days=60):
        """获取行业指数（聚合计算）的历史走势、成交额及估值水平"""
        end_dt = pd.to_datetime(end_date_str)
        start_date = (end_dt - timedelta(days=days*1.5)).strftime("%Y-%m-%d")
        safe_name = sector_name.replace("'", "")
        sql = f"""
            SELECT t1.trade_date AS trade_date, avg(t1.pct_chg) AS sector_chg,
                   sum(t1.amount) AS sector_amt, median(t3.pe_ttm) AS sector_pe
            FROM market_stock_active_daily AS t1
            INNER JOIN rel_stock_sector AS sec ON t1.stock_code = sec.stock_code
            LEFT JOIN stock_fundamental_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            WHERE sec.sector_name = '{safe_name}' AND sec.sector_type = 'SW2'
              AND t1.trade_date >= '{start_date}' AND t1.trade_date <= '{end_date_str}'
            GROUP BY t1.trade_date ORDER BY t1.trade_date
        """
        return self.client.query_df(sql)

    def get_sector_constituents(self, date, sector_name):
        """获取行业成分股表现明细及其基本面指标"""
        safe = sector_name.replace("'", "").split("-")[-1]
        sql = f"""
            SELECT DISTINCT t1.stock_code AS stock_code, t4.name AS stock_name, 
                   t1.pct_chg AS pct_chg, t1.close AS close, t1.amount AS amount, t3.pe_ttm AS pe_ttm
            FROM market_stock_active_daily AS t1
            INNER JOIN rel_stock_sector AS t2 ON t1.stock_code = t2.stock_code
            LEFT JOIN stock_fundamental_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date
            LEFT JOIN meta_stock_info AS t4 ON t1.stock_code = t4.ts_code
            WHERE t1.trade_date = '{date}' AND t2.sector_name LIKE '%{safe}%'
            ORDER BY t1.pct_chg DESC LIMIT 30
        """
        return self.client.query_df(sql)

    def get_sector_data_enhanced(self, date):
        """获取行业热力图数据, 优先查询预计算表, 缺失则动态聚合"""
        df = self.client.query_df(f"SELECT name, pct_chg, heat, rank FROM rank_block_industry WHERE trade_date = '{date}' ORDER BY pct_chg DESC")
        if df.empty:
            sql = f"""
                SELECT t2.sector_name AS name, avg(t1.pct_chg) AS pct_chg, sum(t1.amount) AS heat, 0 AS rank 
                FROM market_stock_active_daily AS t1 
                INNER JOIN rel_stock_sector AS t2 ON t1.stock_code = t2.stock_code 
                WHERE t1.trade_date = '{date}' AND t2.sector_type = 'SW2' 
                GROUP BY t2.sector_name ORDER BY pct_chg DESC LIMIT 50
            """
            return self.client.query_df(sql)
        return df

    def get_market_index_daily(self, date):
        """查询当日各大市场指数的涨跌幅及收盘价"""
        sql = f"""
            SELECT t1.stock_code, t1.stock_name, t1.close, t1.amount, 
                   if(t2.close>0, (t1.close-t2.close)/t2.close*100, 0) AS pct_chg 
            FROM market_index_daily AS t1 
            LEFT JOIN market_index_daily AS t2 
                ON t1.stock_code = t2.stock_code 
                AND t2.trade_date = (SELECT max(trade_date) FROM market_index_daily WHERE trade_date < '{date}') 
            WHERE t1.trade_date = '{date}'
        """
        return self.client.query_df(sql)

    def get_market_snapshot(self, date):
        """获取全市场个股当日涨跌幅及成交额原始快照"""
        return self.client.query_df(f"SELECT stock_code, pct_chg, amount FROM market_stock_active_daily WHERE trade_date = '{date}'")

    def get_market_general_stats(self, date):
        """统计当日市场总体统计指标（总成交、中位数、涨跌家数）"""
        prev = self.get_previous_trading_date(str(date)) or date
        curr_sql = f"SELECT sum(amount) AS total_amt, median(pct_chg) AS median_chg, countIf(pct_chg > 0) AS up_count, countIf(pct_chg < 0) AS down_count FROM market_stock_active_daily WHERE trade_date = '{date}'"
        prev_sql = f"SELECT sum(amount) AS total_amt FROM market_stock_active_daily WHERE trade_date = '{prev}'"
        
        curr_df = self.client.query_df(curr_sql)
        prev_df = self.client.query_df(prev_sql)
        
        if curr_df.empty: 
            return {'total_amt':0, 'median_chg':0, 'up_count':0, 'down_count':0, 'prev_amt':0}
        stats = curr_df.iloc[0].to_dict()
        stats['prev_amt'] = prev_df.iloc[0]['total_amt'] if not prev_df.empty else stats['total_amt']
        return stats

    def get_market_index_history(self, end_date_str, days=30):
        """获取主流市场指数的历史收盘价序列"""
        end = pd.to_datetime(end_date_str)
        start = (end - timedelta(days=days*1.5)).strftime("%Y-%m-%d")
        codes = "'000001.SH','399001.SZ','399006.SZ','000688.SH','000016.SH','000905.SH'"
        return self.client.query_df(f"SELECT trade_date, stock_code, stock_name, close FROM market_index_daily WHERE stock_code IN ({codes}) AND trade_date >= '{start}' AND trade_date <= '{end_date_str}' ORDER BY trade_date")

    def get_daily_limit_stats(self, date):
        """统计当日涨停、炸板及跌停（<-9.5%）个股家数"""
        sql = f"""
            SELECT (SELECT count() FROM kpl_limit_up WHERE trade_date = '{date}') AS limit_up_count, 
                   (SELECT count() FROM kpl_limit_broken WHERE trade_date = '{date}') AS broken_count, 
                   (SELECT countIf(pct_chg < -9.5) FROM market_stock_active_daily WHERE trade_date = '{date}') AS limit_down_count
        """
        return self.client.query_df(sql)

    def get_kpl_ladder(self, date):
        """查询涨停梯队详情：包含连板数、封板时间及题材原因"""
        return self.client.query_df(f"SELECT stock_code, stock_name, streak, reason, plate, limit_time, seal_amt FROM kpl_limit_up WHERE trade_date = '{date}'")

    def get_limit_down_detail(self, date):
        """查询跌停板详情"""
        return self.client.query_df(f"SELECT stock_code, stock_name, streak, reason, plate, limit_time, seal_amt FROM kpl_limit_down WHERE trade_date = '{date}'")

    def get_limit_broken_detail(self, date):
        """查询今日炸板个股及其当前行情数据"""
        sql = f"""
            SELECT t1.stock_code, t1.stock_name, t1.limit_time AS first_limit_time, t1.reason, t1.plate, 
                   t2.close, t2.pct_chg, t2.turnover_rate, t2.amount 
            FROM kpl_limit_broken AS t1 
            LEFT JOIN market_stock_active_daily AS t2 ON t1.stock_code = t2.stock_code AND t1.trade_date = t2.trade_date 
            WHERE t1.trade_date = '{date}' ORDER BY t1.limit_time ASC
        """
        return self.client.query_df(sql)

    def get_sentiment_factor_rank(self, date):
        """查询当日情绪类因子（如连板数、封单额）领先的股票排名"""
        sql = f"""
            SELECT t1.stock_code, t2.name AS stock_name, t1.limit_up_streak, t1.kpl_seal_money, 
                   t1.money_flow_main, t3.pct_chg, t3.close 
            FROM factor_db.factor_sentiment_daily AS t1 
            LEFT JOIN meta_stock_info AS t2 ON t1.stock_code = t2.ts_code 
            LEFT JOIN market_stock_active_daily AS t3 ON t1.stock_code = t3.stock_code AND t1.trade_date = t3.trade_date 
            WHERE t1.trade_date = '{date}' ORDER BY t1.limit_up_streak DESC, t1.kpl_seal_money DESC LIMIT 50
        """
        return self.client.query_df(sql)

    def get_sentiment_trend(self, days=30):
        """获取近期市场涨跌停家数的历史趋势"""
        end = self.get_latest_trade_date()
        start = (end - timedelta(days=days*2)).strftime("%Y-%m-%d")
        return self.client.query_df(f"SELECT trade_date, toInt32(countIf(pct_chg > 9.5)) AS limit_up, toInt32(countIf(pct_chg < -9.5)) AS limit_down FROM market_stock_active_daily WHERE trade_date >= '{start}' GROUP BY trade_date ORDER BY trade_date")

    def get_yesterday_limit_up_performance(self, current_date, prev_date):
        """计算昨日涨停个股在今日的平均收益表现"""
        sql = f"""
            SELECT avg(t1.pct_chg) FROM market_stock_active_daily AS t1 
            WHERE t1.trade_date = '{current_date}' 
              AND t1.stock_code IN (SELECT stock_code FROM kpl_limit_up WHERE trade_date = '{prev_date}')
        """
        try: 
            return self.client.query(sql).result_rows[0][0], None
        except Exception: 
            return 0.0, None