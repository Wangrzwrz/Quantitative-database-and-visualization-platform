## 数据库结构内容概览
- **Layer 1: quant_db** - 日线级标准化行情信息库。
- **Layer 2: stock_3tick_db** - 三秒极买卖盘数据库。
- **Layer 3: factor_db** - 量化因子特征库。

![数据库结构展示图](数据库结构展示图.png)

---

## 1.基础行情库 (quant_db)

### 1.1 数据库结构概览

**执行查询：**

```sql
SELECT
    `table`,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed,
    sum(rows) AS total_rows
FROM system.parts
WHERE (database = 'quant_db') AND active
GROUP BY `table`
ORDER BY total_rows DESC;

```

**查询结果：**
1. **Meta (1-4)**：基础信息定义，作为字典表存在。
2. **Market (5-13)**：全市场行情。
3. **Stock (14)**：个股基本面因子。
4. **Rel (15)**：股票与板块的归属映射。
5. **Kpl (16-19)**：情绪与涨跌停板数据。
6. **Rank (20-25)**：各维度热度排行。

| # | 表名 (Table) | 业务分类 | 压缩后 | 压缩前 | 总行数 (Total Rows) |
| --- | --- | --- | --- | --- | --- |
| 1 | `meta_stock_info` | **元数据** | 430.03 KiB | 1.40 MiB | 5,449 |
| 2 | `meta_sector_info` | **元数据** | 101.72 KiB | 194.66 KiB | 2,840 |
| 3 | `meta_index_info` | **元数据** | 14.39 KiB | 89.68 KiB | 564 |
| 4 | `meta_stock_delisted` | **元数据** | 9.71 KiB | 26.05 KiB | 312 |
| 5 | `market_stock_active_daily` | **行情体系** | 1.06 GiB | 2.74 GiB | 16,236,001 |
| 6 | `market_stock_active_weekly` | **行情体系** | 242.98 MiB | 592.92 MiB | 3,434,927 |
| 7 | `market_stock_active_monthly` | **行情体系** | 61.78 MiB | 139.66 MiB | 809,069 |
| 8 | `market_index_daily` | **行情体系** | 63.96 MiB | 239.95 MiB | 2,280,309 |
| 9 | `market_index_weekly` | **行情体系** | 14.22 MiB | 50.45 MiB | 479,428 |
| 10 | `market_index_monthly` | **行情体系** | 3.40 MiB | 11.91 MiB | 113,136 |
| 11 | `market_stock_delisted_daily` | **行情体系** | 74.61 MiB | 194.03 MiB | 1,124,058 |
| 12 | `market_stock_delisted_weekly` | **行情体系** | 16.93 MiB | 41.17 MiB | 238,497 |
| 13 | `market_stock_delisted_monthly` | **行情体系** | 4.33 MiB | 9.92 MiB | 57,456 |
| 14 | `stock_fundamental_daily` | **基本面** | 1.33 GiB | 3.33 GiB | 15,231,440 |
| 15 | `rel_stock_sector` | **关联关系** | 2.38 MiB | 12.33 MiB | 207,206 |
| 16 | `kpl_limit_up` | **板学数据** | 4.70 MiB | 15.42 MiB | 130,114 |
| 17 | `kpl_limit_up_natural` | **板学数据** | 4.51 MiB | 14.53 MiB | 113,678 |
| 18 | `kpl_limit_broken` | **板学数据** | 1.22 MiB | 3.86 MiB | 47,879 |
| 19 | `kpl_limit_down` | **板学数据** | 1.19 MiB | 3.42 MiB | 42,593 |
| 20 | `rank_fund_etf_sh` | **排行异动** | 3.09 MiB | 14.24 MiB | 171,574 |
| 21 | `rank_fund_etf_sz` | **排行异动** | 2.15 MiB | 9.89 MiB | 118,453 |
| 22 | `rank_fund_otc` | **排行异动** | 1.46 MiB | 8.13 MiB | 80,084 |
| 23 | `rank_block_concept` | **排行异动** | 304.54 KiB | 1.11 MiB | 19,000 |
| 24 | `rank_block_industry` | **排行异动** | 297.13 KiB | 1.07 MiB | 18,981 |
| 25 | `rank_futures` | **排行异动** | 122.30 KiB | 603.75 KiB | 10,835 |


### 1.2 数据库字段详细字典

**执行查询：**

```sql
SELECT
    `table`,
    name,
    type,
    comment
FROM system.columns
WHERE database = 'quant_db'
ORDER BY `table` ASC, position ASC;

```

**字段详情列表：**

#### 1. 行情体系

| 表名 | 核心字段示例 | 数据类型特征 |
| --- | --- | --- |
| `market_index_daily/weekly/monthly` | `open`, `high`, `low`, `close`, `vol`, `amount`, `up_count`, `down_count` | `Nullable(Float64)` |
| `market_stock_active_daily/weekly/monthly` | `open`, `high`, `low`, `close`, `vol`, `amount`, `up_count`, `down_count`, `turnover_rate`, `pct_chg`, `amplitude`, `qfq/hfq` | `Nullable(Float64)` |
| `market_stock_delisted_daily/weekly/monthly` | 已退市股票的历史行情 | `Nullable(Float64)` |

#### 2. 基本面数据

| 表名 | 关键字段 | 说明 |
| --- | --- | --- |
| `stock_fundamental_daily` | `pe`, `pe_ttm`, `pb`, `ps`, `dv_ratio`, `total_mv`, `circ_mv` | 估值与市值指标 |

#### 3. 元数据与关联

| 表名 | 关键字段 | 说明 |
| --- | --- | --- |
| `meta_stock_info` | `ts_code`, `symbol`, `name`, `industry`, `market`, `list_date` | 股票基础信息表 |
| `meta_index_info` | `ts_code`, `name`, `publisher`, `base_point` | 指数定义表 |
| `meta_sector_info` | `sector_id`, `sector_name`, `sector_type` | 板块分类定义 |
| `rel_stock_sector` | `stock_code`, `sector_id`, `sector_name` | 股票-板块映射表 |

#### 4. 板学与异动数据

##### (1) 涨跌停与异动分析

| 表名 | 关键字段 | 业务说明 |
| --- | --- | --- |
| `kpl_limit_up` | `trade_date`, `stock_code`, `stock_name`, `limit_time`, `reason`, `plate`, `seal_amt`, `streak` | 涨停板异动数据 |
| `kpl_limit_up_natural` | `trade_date`, `stock_code`, `stock_name`, `limit_time`, `reason`, `plate`, `seal_amt`, `streak` | 自然涨停异动数据 |
| `kpl_limit_broken` | `trade_date`, `stock_code`, `stock_name`, `limit_time`, `reason`, `plate`, `seal_amt`, `streak` | 曾封涨停但被打开（炸板）数据 |
| `kpl_limit_down` | `trade_date`, `stock_code`, `stock_name`, `limit_time`, `reason`, `plate`, `seal_amt`, `streak` | 跌停板异动数据 |

##### (2) 多维度热度排行

| 表名 | 关键字段 | 业务说明 |
| --- | --- | --- |
| `rank_block_concept` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `reason` | 概念板块热度与排名 |
| `rank_block_industry` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `reason` | 行业板块热度与排名 |
| `rank_fund_etf_sh` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `close`, `source` | 沪市 ETF 排名数据 |
| `rank_fund_etf_sz` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `close`, `source` | 深市 ETF 排名数据 |
| `rank_fund_otc` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `close`, `source` | 场外基金 (OTC) 排名数据 |
| `rank_futures` | `trade_date`, `code`, `name`, `rank`, `heat`, `pct_chg`, `tags`, `reason` | 期货品种热度排名 |



---

## 2.三秒极买卖盘数据库 (stock_3tick_db)

### 2.1 数据库结构概览

**执行查询：**

```sql
SELECT
    `table`,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed,
    sum(rows) AS total_rows
FROM system.parts
WHERE (database = 'stock_3tick_db') AND active
GROUP BY `table`;

```

**查询结果：**

| # | 表名 (Table) |压缩后 | 压缩前 | 总行数 (Total Rows) |
| --- | --- | --- | --- | --- |
| 1 | `ticks` | 346.21 GiB | 659.61 GiB | 26,228,467,861 |

### 2.2 数据库字段详细字典

**执行查询：**

```sql
SELECT
    `table`,
    name,
    type,
    comment
FROM system.columns
WHERE database = 'stock_3tick_db'
ORDER BY
    `table` ASC,
    position ASC;

```

**查询结果：**

| # | 字段名 (Name) | 类型 (Type) | 说明 (Comment) |
| --- | --- | --- | --- |
| 1 | `code` | `FixedString(6)` | 证券代码 |
| 2 | `trade_time` | `DateTime` | 成交时间 |
| 3 | `price` | `Float32` | 当前成交价格 |
| 4 | `volume` | `Int32` | 单笔成交量 |
| 5 | `direction` | `LowCardinality(String)` | 成交方向 |
| 6 | `turnover` | `Float64` | 成交额 |

### 2.3 数据分区情况

#### 2.3.1 表元数据概览

**执行查询：**

```sql
SELECT
    name AS table_name,
    partition_key,
    sorting_key,
    total_rows,
    storage_policy
FROM system.tables
WHERE database = 'stock_3tick_db';

```
**查询结果：**

| table_name | partition_key | sorting_key | total_rows | storage_policy |
| --- | --- | --- | --- | --- |
| **ticks** | `toYYYYMM(trade_time)` | `code, trade_time` | 26,228,467,861 |--- |

#### 2.3.2 各分区详细数据统计

**执行查询：**

```sql
SELECT
    `table`,
    partition,
    count() AS parts_count,
    sum(rows) AS total_rows,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed,
    round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS compress_ratio
FROM system.parts
WHERE (database = 'stock_3tick_db') AND active
GROUP BY `table`, partition
ORDER BY `table` ASC, partition ASC;

```

**查询结果：**

| 序号 | table | partition | parts_count | total_rows | compressed | uncompressed | compress_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ticks | 200006 | 1 | 7,309,044 | 98.93 MiB | 188.22 MiB | 1.9 |
| 2 | ticks | 200007 | 1 | 8,812,945 | 120.28 MiB | 226.94 MiB | 1.89 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 175 | ticks | 201412 | 1 | 79,508,391 | 1.10 GiB | 2.00 GiB | 1.81 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 242 | ticks | 202007 | 1 | 221,552,755 | 3.00 GiB | 5.57 GiB | 1.85 |
| 294 | ticks | 202411 | 1 | 301,611,168 | 4.09 GiB | 7.59 GiB | 1.86 |
| 295 | ticks | 202412 | 1 | 301,157,052 | 4.03 GiB | 7.57 GiB | 1.88 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 306 | ticks | 202511 | 1 | 124,737,957 | 1.66 GiB | 3.14 GiB | 1.89 |



## 3.量化因子特征库 (factor_db)

### 3.1 数据库结构概览

**执行查询：**

```sql
SELECT
    `table`,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed,
    sum(rows) AS total_rows
FROM system.parts
WHERE (database = 'factor_db') AND active
GROUP BY `table`;

```

**查询结果：**

| # | 表名 (Table) | 压缩后 | 压缩前 | 总行数 (Total Rows) |
| --- | --- | --- | --- | --- |
| 1 | `meta_factor_info` | 2.99 KiB | 5.88 KiB | 58 |
| 2 | `factor_sentiment_daily` | 2.12 MiB | 8.63 MiB | 177,940 |
| 3 | `factor_alphas_daily` | 7.61 GiB | 14.03 GiB | 16,236,001 |
| 4 | `factor_technical_daily` | 3.23 GiB | 4.51 GiB | 16,236,001 |
| 5 | `meta_alpha101_info` | 10.63 KiB | 25.28 KiB | 101 |
| 6 | `factor_value_daily` | 843.25 MiB | 1.46 GiB | 15,661,833 |
| 7 | `factor_momentum_daily` | 1.38 GiB | 2.06 GiB | 16,236,001 |

### 3.2 数据库字段详细字典

**执行查询：**

```sql
SELECT
    `table`,
    name,
    type,
    comment
FROM system.columns
WHERE database = 'factor_db'
ORDER BY
    `table` ASC,
    position ASC;

```

**查询结果：**

##### 1. factor_alphas_daily

| # | 字段名 (Name) | 类型 (Type) | 备注 (Comment) |
| --- | --- | --- | --- |
| 1 | `trade_date` | Date |  |
| 2 | `stock_code` | String |  |
| 3-103 | `alpha_001` ~ `alpha_101` | Nullable(Float64) | worldquant alpha101 因子 |

##### 2. factor_momentum_daily

| # | 字段名 (Name) | 类型 (Type) | 备注 (Comment) |
| --- | --- | --- | --- |
| 104 | `trade_date` | Date |  |
| 105 | `stock_code` | String |  |
| 106 | `roc_5` | Nullable(Float64) | 5日涨跌幅 |
| 107 | `roc_20` | Nullable(Float64) | 20日涨跌幅 |
| 108 | `roc_60` | Nullable(Float64) | 60日涨跌幅 |
| 109 | `volatility_20` | Nullable(Float64) | 20日波动率 |
| 110 | `turnover_mean_5` | Nullable(Float64) | 5日平均换手 |
| 111 | `amplitude_mean_5` | Nullable(Float64) | 5日平均振幅 |
| 112 | `pos_20` | Nullable(Float64) |  |
| 113 | `pos_60` | Nullable(Float64) |  |
| 114 | `mom_acc_5` | Nullable(Float64) |  |
| 115 | `linear_reg_slope_20` | Nullable(Float64) |  |
| 116 | `vr_26` | Nullable(Float64) |  |
| 117 | `skew_20` | Nullable(Float64) |  |
| 118 | `kurt_20` | Nullable(Float64) |  |

##### 3. factor_sentiment_daily

| # | 字段名 (Name) | 类型 (Type) | 备注 (Comment) |
| --- | --- | --- | --- |
| 119 | `trade_date` | Date |  |
| 120 | `stock_code` | String |  |
| 121 | `limit_up_streak` | Int32 | 连板高度 (0表示未涨停) |
| 122 | `is_limit_up` | Int8 | 是否涨停 (0/1) |
| 123 | `is_limit_broken` | Int8 | 是否炸板 (0/1) |
| 124 | `kpl_seal_money` | Float64 | 封单金额 (直接来自KPL) |
| 125 | `kpl_net_buy_ratio` | Nullable(Float64) | 龙虎榜净买入/成交额 |
| 126 | `money_flow_main` | Nullable(Float64) | 主力资金净流入 |

##### 4. factor_technical_daily

| # | 字段名 (Name) | 类型 (Type) | 备注 (Comment) |
| --- | --- | --- | --- |
| 127 | `trade_date` | Date |  |
| 128 | `stock_code` | String |  |
| 129 | `ma_5` | Nullable(Float64) | 5日均线 |
| 130 | `ma_20` | Nullable(Float64) |  |
| 131 | `ma_60` | Nullable(Float64) |  |
| 132 | `bias_20` | Nullable(Float64) | 乖离率 |
| 133-159 | `rsi_14`, `macd_diff`, `boll`, `kdj`, `cci` 等 | Nullable(Float64) | 常用技术分析指标 |

##### 5. factor_value_daily

| # | 字段名 (Name) | 类型 (Type) | 备注 (Comment) |
| --- | --- | --- | --- |
| 160 | `trade_date` | Date |  |
| 161 | `stock_code` | String |  |
| 162 | `ln_market_cap` | Nullable(Float64) | 对数总市值 |
| 163 | `ep_ttm` | Nullable(Float64) | 盈利收益率 (1/PE) |
| 164 | `bp_lr` | Nullable(Float64) | 账面市值比 (1/PB) |
| 165 | `sp_ttm` | Nullable(Float64) | 销售市值比 (1/PS) |
| 166 | `dividend_yield` | Nullable(Float64) | 股息率 |
| 167 | `roe_ttm` | Nullable(Float64) |  |
| 168 | `yoy_net_profit` | Nullable(Float64) |  |
| 169 | `pe_zscore_60` | Nullable(Float64) |  |
| 170 | `pb_zscore_60` | Nullable(Float64) |  |

##### 6. 元数据表

| 表名 (Table) | 字段名 (Name) | 备注 (Comment) |
| --- | --- | --- |
| `meta_alpha101_info` | `alpha_id`, `formula`, `description`... |  Alpha 101 定义详情 |
| `meta_factor_info` | `factor_name`, `category`, `formula`... | 通用因子字典 |




---

## 附录：

### `quant_db` 数据库内容样本详情

#### 一、 元数据维度表

##### 1. 股票基础信息 `meta_stock_info`

| `ts_code` | `name` | `area` | `industry` | `market` | `list_date` | `act_controller` |
| --- | --- | --- | --- | --- | --- | --- |
| 000001.SZ | 平安银行 | 深圳 | 银行 | 主板 | 19910403 | Richard C. Blum |
| 000002.SZ | 万科A | 深圳 | 全国地产 | 主板 | 19910129 | 无实际控制人 |
| 000004.SZ | *ST国华 | 深圳 | 软件服务 | 主板 | 19910114 | 中国农业大学 |

##### 2. 指数基础信息 `meta_index_info`

| `ts_code` | `name` | `market` | `publisher` | `category` | `base_date` | `list_date` |
| --- | --- | --- | --- | --- | --- | --- |
| 000001.SH | 上证指数 | SSE | 中证指数有限公司 | 综合指数 | 19901219 | 19910715 |
| 000002.SH | 上证A指 | SSE | 中证指数有限公司 | 规模指数 | 19901219 | 19920221 |

##### 3. 板块定义信息 `meta_sector_info`

| `sector_id` | `sector_name` | `sector_type` | `source_file` | `updated_at` |
| --- | --- | --- | --- | --- |
| 1cfa02f0697ad773 | CSRC1批发和零售业 | CSRC_1 | CSRC1批发和零售业 | 2026-01-30 |
| 206d788f95aaaa22 | CSRC1制造业 | CSRC_1 | CSRC1制造业 | 2026-01-30 |

##### 4. 退市股票记录 `meta_stock_delisted`

| `ts_code` | `symbol` | `name` | `list_date` | `delist_date` |
| --- | --- | --- | --- | --- |
| 000003.SZ | 000003 | PT金田A(退) | 19910703 | 20020614 |
| 000005.SZ | 000005 | ST星源(退) | 19901210 | 20240426 |

#### 二、 全市场行情体系

##### 1. 股票日线行情 `market_stock_*`

| `trade_date` | `stock_code` | `open` | `high` | `low` | `close` | `vol` | `pct_chg` | `turnover_rate` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 600601.SH | 185.3 | 185.3 | 185.3 | 185.3 | 50.0 | 270.6 | 2.5 |
| 1990-12-20 | 600601.SH | 185.3 | 194.6 | 185.3 | 194.6 | 21.0 | 5.02 | 1.05 |

##### 2. 指数日线行情 `market_index_*`

| `trade_date` | `stock_code` | `stock_name` | `open` | `close` | `vol` | `up_count` | `down_count` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 000001.SH | 上证指数 | 96.05 | 99.98 | 1032.0 | 8.0 | 0.0 |
| 1990-12-20 | 000001.SH | 上证指数 | 104.3 | 104.39 | 32768.5 | 3.0 | 0.0 |

#### 三、 个股基本面

##### 1. 个股每日基本面指标 `stock_fundamental_*`

| `trade_date` | `stock_code` | `pe_ttm` | `pb` | `dv_ratio` | `total_mv` | `circ_mv` |
| --- | --- | --- | --- | --- | --- | --- |
| 1996-06-28 | 000403.SZ | 42.6276 | 5.5349 | None | 35619.9 | 13320.0 |

#### 四、 关联关系

##### 1. 股票与板块映射 `rel_stock_sector`

| `stock_code` | `sector_id` | `sector_name` | `sector_type` |
| --- | --- | --- | --- |
| 000001.SZ | a7731086ee5a60bc | CSRC1金融业 | CSRC_1 |
| 000001.SZ | 735e2cb6b6563a78 | 中证100 | D_CONCEPT |

#### 五、 板学与情绪异动

##### 1. 涨停/跌停板异动系列 `kpl_limit_*`

| 表名 | 关键示例数据 (`trade_date`, `stock_name`, `limit_time`, `reason`, `streak`) |
| --- | --- |
| `kpl_limit_up` | `2018-01-02`, `上峰水泥`, `13:23:57`, `地产链`, `首板` |
| `kpl_limit_broken` | `2018-01-02`, `泰禾集团`, `09:36:57`, `地产链 (炸板)`, `-` |
| `kpl_limit_down` | `2018-01-02`, `金岭矿业`, `-`, `有色金属`, `-` |

#### 六、 排行与热度数据

##### 1. 行业与概念热度 `rank_block_*`

| `trade_date` | `name` | `rank` | `pct_chg` | `reason` |
| --- | --- | --- | --- | --- |
| 2023-11-21 | 短剧游戏 | 1 | 3.14 | 短剧出海爆发 |
| 2023-11-21 | 传媒 | 1 | 2.02 | 行业热度提升 |

##### 2. 基金与期货排行 `rank_fund_*`

| 表名 | 示例项目 (`code`, `name`, `rank`, `pct_chg`) |
| --- | --- |
| `rank_fund_otc` | `004685.OF`, `金元顺安元启`, `1`, `0.7%` |
| `rank_futures` | `SA2401`, `纯碱2401`, `1`, `1.57%` |



### `stock_3tick_db` 数据库内容样本详情

##### 股票交易 Tick 数据表

| 证券代码 (code) | 交易时间 (trade_time) | 价格 (price) | 成交量 (volume) | 买卖方向 (direction) |
| --- | --- | --- | --- | --- |
| 000001 | 2000-06-09 09:30:00 | 18.89 | 317 | 买盘 |
| 000001 | 2000-06-09 09:30:03 | 18.90 | 1032 | 买盘 |
| 000001 | 2000-06-09 09:30:06 | 18.90 | 39 | 卖盘 |



### `factor_db` 数据库内容样本详情

##### 1. Alpha 101 日频因子表 `factor_alphas_daily`

> **注：** 由于字段极多（101个因子），此处仅展示前两个样本的核心列及部分代表性因子。

| 交易日期 (trade_date) | 股票代码 (stock_code) | alpha_001 | alpha_007 | alpha_021 | alpha_101 |
| --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 600601.SH | NaN | -1.0 | -1.0 | 0.0 |
| 1990-12-19 | 600602.SH | NaN | -1.0 | -1.0 | 0.9999 |
| 1990-12-19 | 600651.SH | NaN | -1.0 | -1.0 | 0.0 |

##### 2. 动量因子表 `factor_momentum_daily`

| 交易日期 (trade_date) | 股票代码 (stock_code) | roc_5 | roc_20 | 波动率 (volatility_20) | 换手率 (turnover_mean_5) |
| --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 600601.SH | None | None | None | None |
| 1990-12-19 | 600602.SH | None | None | None | None |
| 1990-12-20 | 600601.SH | None | None | None | None |

##### 3. 市场情绪表 `factor_sentiment_daily`

| 交易日期 (trade_date) | 股票代码 (stock_code) | 连板高度 | 是否涨停 | 是否炸板 | 封单金额 (元) |
| --- | --- | --- | --- | --- | --- |
| 2018-01-02 | 000672.SZ | 1 | 1 | 0 | 0.0 |
| 2018-01-02 | 000703.SZ | 1 | 1 | 0 | 0.0 |
| 2018-01-02 | 000732.SZ | 0 | 0 | 1 | 0.0 |

##### 4. 技术指标表 `factor_technical_daily`

| 交易日期 (trade_date) | 股票代码 (stock_code) | MA_5 | MA_20 | MACD_DIFF | TRIX_12 |
| --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 600601.SH | None | None | 0.0 | None |
| 1990-12-19 | 600602.SH | None | None | 0.0 | None |
| 1990-12-20 | 600601.SH | None | None | 0.4173 | 0.7976 |

##### 5. 价值/基本面因子表 `factor_value_daily`

| 交易日期 (trade_date) | 股票代码 (stock_code) | 对数市值 | EP_TTM | BP_LR | 股息率 |
| --- | --- | --- | --- | --- | --- |
| 1990-12-19 | 600601.SH | None | None | None | None |
| 1990-12-19 | 600602.SH | None | None | None | None |
| 1990-12-20 | 600601.SH | None | None | None | None |

##### 6. Alpha 101 元数据定义表 `meta_alpha101_info`

| 因子ID | 因子公式 (Formula) | 因子描述 | 关键逻辑 |
| --- | --- | --- | --- |
| `alpha_001` | rank(ts_argmax(...)) | 极值距离反转 | 关注“极端行情”发生日期，越近反转概率越高。 |
| `alpha_002` | -1 * correlation(...) | 量价背离 | 成交量变化与日内涨幅负相关意味着背离。 |
| `alpha_003` | -1 * correlation(...) | 开盘量价相关 | 开盘价位与成交量的关系。 |

##### 7. 通用因子元数据表 `meta_factor_info`

| 因子字段名 | 分类 | 含义描述 | 计算逻辑 | 创建时间 |
| --- | --- | --- | --- | --- |
| `is_limit_broken` | emotion | 是否炸板 | Exist in kpl_limit_broken | 2026-01-31 |
| `is_limit_up` | emotion | 是否涨停 | Exist in kpl_limit_up | 2026-01-31 |
| `kpl_seal_money` | emotion | 封单金额 | Direct from kpl_limit_up | 2026-01-31 |