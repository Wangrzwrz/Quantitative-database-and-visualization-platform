### `future_db` 数据库建表语句 (DDL)

```sql
-- 1. 商品1分_真实交割月表
CREATE TABLE IF NOT EXISTS future_db.commodity_min1_actual
(
    `market` LowCardinality(String) COMMENT '市场代码, 如 DC, CZC, SHFE',
    `contract` String COMMENT '合约代码, 如 a0501, rb2405',
    `datetime` DateTime COMMENT 'K线时间',
    `open` Float64 COMMENT '开盘价',
    `high` Float64 COMMENT '最高价',
    `low` Float64 COMMENT '最低价',
    `close` Float64 COMMENT '收盘价',
    `volume` Float64 COMMENT '成交量',
    `amount` Float64 COMMENT '成交额',
    `open_interest` Float64 COMMENT '持仓量'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(datetime)
ORDER BY (contract, datetime)
SETTINGS index_granularity = 8192;

-- 2. 股指1分_真实交割月表
CREATE TABLE IF NOT EXISTS future_db.index_min1_actual
(
    `market` LowCardinality(String) COMMENT '市场代码, 如 SF',
    `contract` String COMMENT '合约代码, 如 IF1005',
    `datetime` DateTime COMMENT 'K线时间',
    `open` Float64 COMMENT '开盘价',
    `high` Float64 COMMENT '最高价',
    `low` Float64 COMMENT '最低价',
    `close` Float64 COMMENT '收盘价',
    `volume` Float64 COMMENT '成交量',
    `amount` Float64 COMMENT '成交额',
    `open_interest` Float64 COMMENT '持仓量'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(datetime)
ORDER BY (contract, datetime)
SETTINGS index_granularity = 8192;

-- 3. 商品1分_连续合约表
CREATE TABLE IF NOT EXISTS future_db.commodity_min1_continuous
(
    `market` LowCardinality(String) COMMENT '市场代码',
    `symbol` String COMMENT '品种基础代码, 如 TF, m, rb',
    `contract_type` String COMMENT '连续类型, 如 主力连续, 次主力连续',
    `datetime` DateTime COMMENT 'K线时间',
    `open` Float64 COMMENT '开盘价',
    `high` Float64 COMMENT '最高价',
    `low` Float64 COMMENT '最低价',
    `close` Float64 COMMENT '收盘价',
    `volume` Float64 COMMENT '成交量',
    `amount` Float64 COMMENT '成交额',
    `open_interest` Float64 COMMENT '持仓量'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(datetime)
ORDER BY (symbol, contract_type, datetime)
SETTINGS index_granularity = 8192;

-- 4. 股指1分_连续合约表
CREATE TABLE IF NOT EXISTS future_db.index_min1_continuous
(
    `market` LowCardinality(String) COMMENT '市场代码',
    `symbol` String COMMENT '品种基础代码, 如 IF, IC, IM',
    `contract_type` String COMMENT '连续类型, 如 当季连续, 下季连续',
    `datetime` DateTime COMMENT 'K线时间',
    `open` Float64 COMMENT '开盘价',
    `high` Float64 COMMENT '最高价',
    `low` Float64 COMMENT '最低价',
    `close` Float64 COMMENT '收盘价',
    `volume` Float64 COMMENT '成交量',
    `amount` Float64 COMMENT '成交额',
    `open_interest` Float64 COMMENT '持仓量'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(datetime)
ORDER BY (symbol, contract_type, datetime)
SETTINGS index_granularity = 8192;
```


### 二、 核心架构设计

1. 存储引擎: 使用了 ClickHouse 的 `MergeTree` 引擎。

2. 分区策略：`PARTITION BY toYYYYMM(datetime)`，采用**按自然月（YYYYMM）**进行物理分区。

3. 排序与索引设计：`ORDER BY`
    * 真实合约表：`ORDER BY (contract, datetime)`
    * 连续合约表：`ORDER BY (symbol, contract_type, datetime)`
