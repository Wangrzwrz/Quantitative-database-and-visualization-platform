import clickhouse_connect
import pandas as pd
from datetime import datetime

class QuantDB:
    """量化数据库交互类"""

    def __init__(self, host='localhost', port=8123, user='default', password='', database='quant_db'):
        """初始化数据库连接"""
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
            return '000001.SZ'
        code = str(code).strip().upper()
        if code.endswith(('.SZ', '.SH', '.BJ')):
            return code
        return f"{code}.SH" if code.startswith('6') else f"{code}.SZ"

    def get_latest_trade_date(self):
        """获取数据库中最新交易日期"""
        sql = "SELECT max(trade_date) FROM market_stock_active_daily"
        try:
            res = self.client.query(sql).result_rows
            return res[0][0] if res else datetime.now().date()
        except Exception:
            return datetime.now().date()

    def get_stock_info(self, code):
        """查询个股元数据(名称、行业、地域、上市日期)"""
        code = self._fix_code(code)
        sql = f"""
            SELECT name, industry, area, list_date 
            FROM meta_stock_info 
            WHERE ts_code = '{code}' 
            LIMIT 1
        """
        try:
            df = self.client.query_df(sql)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        return {'name': code, 'industry': '-', 'area': '-', 'list_date': '-'}

    def get_kline(self, code, start_date, end_date=None):
        """获取指定时间范围的日线前复权K线数据"""
        code = self._fix_code(code)
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        sql = f"""
            SELECT trade_date, open_qfq AS open, close_qfq AS close, 
                   high_qfq AS high, low_qfq AS low, vol, amount, 
                   pct_chg, turnover_rate
            FROM market_stock_active_daily
            WHERE stock_code = '{code}' 
              AND trade_date >= '{start_date}' 
              AND trade_date <= '{end_date}'
            ORDER BY trade_date
        """
        return self.client.query_df(sql)

    def get_limit_up_ladder(self, date):
        """获取涨停梯队数据，并解析连板高度"""
        sql = f"""
            SELECT 
                stock_code, stock_name, streak, reason, limit_time, seal_amt,
                CASE 
                    WHEN streak LIKE '%连板' THEN toInt32OrZero(substring(streak, 1, length(streak)-3))
                    WHEN streak = '首板' THEN 1
                    ELSE 1 
                END AS height
            FROM kpl_limit_up
            WHERE trade_date = '{date}'
            ORDER BY height DESC, limit_time ASC
        """
        return self.client.query_df(sql)

    def get_market_sentiment_summary(self, date):
        """统计当日涨停、炸板及跌停（<-9.5%）家数"""
        up_sql = f"SELECT count() FROM kpl_limit_up WHERE trade_date='{date}'"
        broken_sql = f"SELECT count() FROM kpl_limit_broken WHERE trade_date='{date}'"
        down_sql = f"SELECT countIf(pct_chg < -9.5) FROM market_stock_active_daily WHERE trade_date='{date}'"
        
        return {
            'up': self.client.query(up_sql).result_rows[0][0],
            'broken': self.client.query(broken_sql).result_rows[0][0],
            'down': self.client.query(down_sql).result_rows[0][0]
        }

    def get_screener_data(self, date):
        """多表关联查询：获取涵盖基本面、估值及动量因子的全市场数据"""
        sql = f"""
            SELECT 
                base.stock_code, base.pct_chg, base.close, base.amount, base.turnover_rate,
                funda.total_mv / 100000000 AS total_mv_yi,
                funda.pe_ttm,
                val.pb_zscore_60,
                val.roe_ttm,
                val.dividend_yield,
                mom.roc_20 AS month_mom,
                mom.roc_60 AS quarter_mom,
                mom.volatility_20
            FROM market_stock_active_daily AS base
            LEFT JOIN stock_fundamental_daily AS funda 
                ON base.stock_code = funda.stock_code AND base.trade_date = funda.trade_date
            LEFT JOIN factor_db.factor_value_daily AS val 
                ON base.stock_code = val.stock_code AND base.trade_date = val.trade_date
            LEFT JOIN factor_db.factor_momentum_daily AS mom 
                ON base.stock_code = mom.stock_code AND base.trade_date = mom.trade_date
            WHERE base.trade_date = '{date}'
        """
        return self.client.query_df(sql)

    def get_sector_heatmap(self, date):
        """获取行业板块的涨跌幅、热度及排名数据"""
        sql = f"""
            SELECT name, pct_chg, heat, rank 
            FROM rank_block_industry
            WHERE trade_date = '{date}'
            ORDER BY pct_chg DESC
        """
        return self.client.query_df(sql)