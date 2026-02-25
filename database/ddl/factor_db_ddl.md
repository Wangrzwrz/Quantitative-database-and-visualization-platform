### `factor_db` 数据库建表语句 (DDL)

**执行查询：**

```sql
SELECT
    name AS table_name,
    create_table_query
FROM system.tables
WHERE database = 'factor_db';

```

**查询结果：**
#### 1. Alpha 101 因子表 (`factor_alphas_daily`)

```sql
CREATE TABLE factor_db.factor_alphas_daily
(
    `trade_date` Date,
    `stock_code` String,
    `alpha_001` Nullable(Float64),
    `alpha_002` Nullable(Float64),
    /* ... 中间省略 alpha_003 至 alpha_100 ... */
    `alpha_101` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 2. 动量因子表 (`factor_momentum_daily`)

```sql
CREATE TABLE factor_db.factor_momentum_daily
(
    `trade_date` Date,
    `stock_code` String,
    `roc_5` Nullable(Float64) COMMENT '5日涨跌幅',
    `roc_20` Nullable(Float64) COMMENT '20日涨跌幅 (月度动量)',
    `roc_60` Nullable(Float64) COMMENT '60日涨跌幅 (季度动量)',
    `volatility_20` Nullable(Float64) COMMENT '20日波动率',
    `turnover_mean_5` Nullable(Float64) COMMENT '5日平均换手',
    `amplitude_mean_5` Nullable(Float64) COMMENT '5日平均振幅',
    `pos_20` Nullable(Float64),
    `pos_60` Nullable(Float64),
    `mom_acc_5` Nullable(Float64),
    `linear_reg_slope_20` Nullable(Float64),
    `vr_26` Nullable(Float64),
    `skew_20` Nullable(Float64),
    `kurt_20` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 3. 市场情绪表 (`factor_sentiment_daily`)

```sql
CREATE TABLE factor_db.factor_sentiment_daily
(
    `trade_date` Date,
    `stock_code` String,
    `limit_up_streak` Int32 COMMENT '连板高度 (0表示未涨停)',
    `is_limit_up` Int8 COMMENT '是否涨停 (0/1)',
    `is_limit_broken` Int8 COMMENT '是否炸板 (0/1)',
    `kpl_seal_money` Float64 COMMENT '封单金额 (直接来自KPL)',
    `kpl_net_buy_ratio` Nullable(Float64) COMMENT '龙虎榜净买入/成交额',
    `money_flow_main` Nullable(Float64) COMMENT '主力资金净流入'
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 4. 技术指标表 (`factor_technical_daily`)

```sql
CREATE TABLE factor_db.factor_technical_daily
(
    `trade_date` Date,
    `stock_code` String,
    `ma_5` Nullable(Float64) COMMENT '5日均线',
    `ma_20` Nullable(Float64),
    `ma_60` Nullable(Float64),
    `bias_20` Nullable(Float64) COMMENT '乖离率',
    `rsi_14` Nullable(Float64),
    `macd_diff` Nullable(Float64),
    `macd_dea` Nullable(Float64),
    `kdj_k` Nullable(Float64),
    `kdj_d` Nullable(Float64),
    `atr_14` Nullable(Float64),
    `boll_upper` Nullable(Float64),
    `boll_lower` Nullable(Float64),
    /* ... 篇幅原因省略部分指标 ... */
    `mass_25` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 5. 价值/基本面因子表 (`factor_value_daily`)

```sql
CREATE TABLE factor_db.factor_value_daily
(
    `trade_date` Date,
    `stock_code` String,
    `ln_market_cap` Nullable(Float64) COMMENT '对数总市值 (Size因子)',
    `ep_ttm` Nullable(Float64) COMMENT '盈利收益率 (1/PE)',
    `bp_lr` Nullable(Float64) COMMENT '账面市值比 (1/PB)',
    `sp_ttm` Nullable(Float64) COMMENT '销售市值比 (1/PS)',
    `dividend_yield` Nullable(Float64) COMMENT '股息率',
    `roe_ttm` Nullable(Float64),
    `yoy_net_profit` Nullable(Float64),
    `pe_zscore_60` Nullable(Float64),
    `pb_zscore_60` Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, stock_code)
SETTINGS index_granularity = 8192;

```

#### 6. 因子定义元数据表 (`meta_alpha101_info` & `meta_factor_info`)

```sql
/* Alpha 101 详情表 */
CREATE TABLE factor_db.meta_alpha101_info
(
    `alpha_id` String COMMENT '因子ID',
    `formula` String COMMENT '原始公式',
    `description` String COMMENT '因子逻辑简述',
    `category` String DEFAULT 'alpha101',
    `created_at` DateTime DEFAULT now(),
    `critical_logic` String COMMENT '关键逻辑说明'
)
ENGINE = MergeTree
ORDER BY alpha_id;

/* 通用因子详情表 */
CREATE TABLE factor_db.meta_factor_info
(
    `factor_name` String COMMENT '因子字段名, 如 rsi_14',
    `category` String COMMENT '分类: technical, value, emotion...',
    `description` String COMMENT '因子含义描述',
    `formula` String COMMENT '计算公式逻辑',
    `creator` String DEFAULT 'system',
    `created_at` DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (category, factor_name);

```

---

* **主键选择**：所有因子表均以 `(trade_date, stock_code)` 为主键，利于进行“截面分析”，即在同一时间点对比不同股票的因子表现。
