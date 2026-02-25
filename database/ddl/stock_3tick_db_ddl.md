### `stock_3tick_db` 数据库建表语句 (DDL) 

**执行查询：**

```sql
SELECT
    name AS table_name,
    create_table_query
FROM system.tables
WHERE database = 'stock_3tick_db';

```

**查询结果：**

```sql
CREATE TABLE stock_3tick_db.ticks
(
    `code` FixedString(6),
    `trade_time` DateTime,
    `price` Float32,
    `volume` Int32,
    `direction` LowCardinality(String),
    /* 自动计算列：成交额 = 价格 * 成交量 * 100 */
    `turnover` Float64 MATERIALIZED (price * volume) * 100
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trade_time)
ORDER BY (code, trade_time)
SETTINGS index_granularity = 8192, storage_policy = 'default';

```

---


* **存储引擎**：采用 ClickHouse 核心 `MergeTree` 引擎，支持高效的分析查询。
* **分区策略 (`PARTITION BY`)**：按月（`toYYYYMM(trade_time)`）进行分区，这有助于在按时间范围查询时快速剔除无关数据，并方便进行过往数据的冷热管理。
* **排序/索引 (`ORDER BY`)**：以 `(code, trade_time)` 作为主键。这种设计非常适合金融场景：
  1. 能够快速定位特定股票的所有交易记录。
  2. 同一股票的数据在物理上按时间顺序存储，极大地加速了时序分析计算。


* **物化列 (`MATERIALIZED`)**：`turnover` 字段通过公式自动计算，不随 `INSERT` 显式写入，而是在存储时自动计算，节省了应用层的逻辑开销。
* **低基数优化 (`LowCardinality`)**：对 `direction`（买卖方向）使用低基数编码，可以有效减少存储占用并提升过滤性能。