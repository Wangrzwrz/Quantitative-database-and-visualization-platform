### `quant_db` 数据库建表语句 (DDL)


**执行查询：**

```sql
SELECT
    name AS table_name,
    create_table_query
FROM system.tables
WHERE database = 'quant_db';

```

**查询结果：**

##### 1. meta_info_*

```sql
/* 1.1 股票基础信息表 */
CREATE TABLE quant_db.meta_stock_info
(
    `ts_code` String,
    `symbol` String,
    `name` String,
    `area` String,
    `industry` String,
    `fullname` String,
    `enname` String,
    `cn_spell` String,
    `market` String,
    `exchange` String,
    `list_date` String,
    `act_controller` String,
    `act_ent_type` String
)
ENGINE = MergeTree
ORDER BY ts_code
SETTINGS index_granularity = 8192;

/* 1.2 指数基础信息表 */
CREATE TABLE quant_db.meta_index_info
(
    `ts_code` String,
    `name` String,
    `market` String,
    `publisher` String,
    `category` String,
    `base_date` String,
    `base_point` Float64,
    `list_date` String,
    `symbol_num` String,
    `market_id` Nullable(Float64)
)
ENGINE = MergeTree
ORDER BY ts_code
SETTINGS index_granularity = 8192;

/* 1.3 退市股票基础信息表 */
CREATE TABLE quant_db.meta_stock_delisted
(
    `ts_code` String,
    `symbol` String,
    `name` String,
    `area` String,
    `industry` String,
    `list_date` String,
    `delist_date` String
)
ENGINE = MergeTree
ORDER BY ts_code
SETTINGS index_granularity = 8192;

/* 1.4 板块/行业定义信息表 */
CREATE TABLE quant_db.meta_sector_info
(
    `sector_id` String,
    `sector_name` String,
    `sector_type` LowCardinality(String),
    `source_file` String,
    `updated_at` DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (sector_type, sector_id)
SETTINGS index_granularity = 8192;

```

##### 2. market_*

```sql
/* 2.1 指数日行情 */
CREATE TABLE quant_db.market_index_daily
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `up_count` Nullable(Float64),
    `down_count` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.2 指数周行情 */
CREATE TABLE quant_db.market_index_weekly
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `up_count` Nullable(Float64),
    `down_count` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.3 指数月行情 */
CREATE TABLE quant_db.market_index_monthly
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `up_count` Nullable(Float64),
    `down_count` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.4 活跃个股日行情 (含复权) */
CREATE TABLE quant_db.market_stock_active_daily
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.5 活跃个股周行情 */
CREATE TABLE quant_db.market_stock_active_weekly
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.6 活跃个股月行情 */
CREATE TABLE quant_db.market_stock_active_monthly
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.7 已退市个股日行情 */
CREATE TABLE quant_db.market_stock_delisted_daily
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.8 已退市个股周行情 */
CREATE TABLE quant_db.market_stock_delisted_weekly
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

/* 2.9 已退市个股月行情 */
CREATE TABLE quant_db.market_stock_delisted_monthly
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `amplitude` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `change` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `open_qfq` Nullable(Float64),
    `high_qfq` Nullable(Float64),
    `low_qfq` Nullable(Float64),
    `close_qfq` Nullable(Float64),
    `open_hfq` Nullable(Float64),
    `high_hfq` Nullable(Float64),
    `low_hfq` Nullable(Float64),
    `close_hfq` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

```

##### 3. stock_fundamental_daily

```sql
/* 3.1 个股每日财务与基本面指标 */
CREATE TABLE quant_db.stock_fundamental_daily
(
    `trade_date` Date,
    `stock_code` String,
    `open` Nullable(Float64),
    `high` Nullable(Float64),
    `low` Nullable(Float64),
    `close` Nullable(Float64),
    `pre_close` Nullable(Float64),
    `change` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `vol` Nullable(Float64),
    `amount` Nullable(Float64),
    `turnover_rate` Nullable(Float64),
    `turnover_rate_f` Nullable(Float64),
    `volume_ratio` Nullable(Float64),
    `pe` Nullable(Float64),
    `pe_ttm` Nullable(Float64),
    `pb` Nullable(Float64),
    `ps` Nullable(Float64),
    `ps_ttm` Nullable(Float64),
    `dv_ratio` Nullable(Float64),
    `dv_ratio_ttm` Nullable(Float64),
    `total_share` Nullable(Float64),
    `float_share` Nullable(Float64),
    `free_share` Nullable(Float64),
    `total_mv` Nullable(Float64),
    `circ_mv` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (stock_code, trade_date)
SETTINGS index_granularity = 8192;

```

##### 4. rel_stock_sector

```sql
/* 4.1 股票与板块(行业/概念)的归属映射表 */
CREATE TABLE quant_db.rel_stock_sector
(
    `stock_code` String,
    `sector_id` String,
    `sector_name` String,
    `sector_type` LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (stock_code, sector_type, sector_id)
SETTINGS index_granularity = 8192;

```

##### 5. kpl_*

```sql
/* 5.1 炸板记录 */
CREATE TABLE quant_db.kpl_limit_broken
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `limit_time` String,
    `reason` String,
    `plate` String,
    `seal_amt` String,
    `streak` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

/* 5.2 跌停记录 */
CREATE TABLE quant_db.kpl_limit_down
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `limit_time` String,
    `reason` String,
    `plate` String,
    `seal_amt` String,
    `streak` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

/* 5.3 涨停记录 */
CREATE TABLE quant_db.kpl_limit_up
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `limit_time` String,
    `reason` String,
    `plate` String,
    `seal_amt` Float64,
    `streak` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

/* 5.4 自然涨停记录 */
CREATE TABLE quant_db.kpl_limit_up_natural
(
    `trade_date` Date,
    `stock_code` String,
    `stock_name` String,
    `limit_time` String,
    `reason` String,
    `plate` String,
    `seal_amt` String,
    `streak` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 6. rank_*

```sql
/* 6.1 概念板块热度排行 */
CREATE TABLE quant_db.rank_block_concept
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `tags` String,
    `reason` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

/* 6.2 行业板块热度排行 */
CREATE TABLE quant_db.rank_block_industry
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `tags` String,
    `reason` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

/* 6.3 沪市基金/ETF热度排行 */
CREATE TABLE quant_db.rank_fund_etf_sh
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `close` Nullable(Float64),
    `source` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

/* 6.4 深市基金/ETF热度排行 */
CREATE TABLE quant_db.rank_fund_etf_sz
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `close` Nullable(Float64),
    `source` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

/* 6.5 场外基金热度排行 */
CREATE TABLE quant_db.rank_fund_otc
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `close` Nullable(Float64),
    `source` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

/* 6.6 期货品种热度排行 */
CREATE TABLE quant_db.rank_futures
(
    `trade_date` Date,
    `code` String,
    `name` String,
    `rank` Int32,
    `heat` Nullable(Float64),
    `pct_chg` Nullable(Float64),
    `tags` String,
    `reason` String
)
ENGINE = MergeTree
PARTITION BY toYear(trade_date)
ORDER BY (trade_date, rank)
SETTINGS index_granularity = 8192;

```

---

1. **分区策略**：绝大部分时序数据采用了 `toYear(trade_date)` 分区，相比于之前的 `toYYYYMM`，这在处理多年跨度的中长线策略分析时，可以减少分区数量，提升扫描效率。
2. **主键索引**：
   * **行情类** 以 `(stock_code, trade_date)` 排序，利于提取单只股票的历史序列。
   * **情绪/排行类** 以 `(trade_date, stock_code/rank)` 排序，利于进行截面热度分析。
3. **类型优化**：`rel_stock_sector` 和 `meta_sector_info` 中的 `sector_type` 使用了 `LowCardinality(String)`，对于“行业”、“概念”这种重复率高的分类字段能极大压缩空间并加速查询。
