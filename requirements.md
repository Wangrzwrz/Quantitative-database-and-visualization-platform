# 项目依赖清单

本清单涵盖了量化数据库与前端平台在生产环境部署时所需的各项依赖，分为操作系统、数据库底层、Python 开发环境及前端框架四个维度。

## 1. Linux 系统环境依赖 (OS & Infrastructure)

系统层承担了文件管理、自动化运维及高性能 I/O 调度的职责。

* **操作系统**: Ubuntu 20.04+ 或 CentOS 7.9+ (推荐 64-bit)。
* **内核优化**: 建议开启 `Transparent Huge Pages (THP)` 的内存优化。
* **系统工具**:
  * `bash`: 用于执行 `optimize.sh` 分区治理脚本。
  * `curl` / `wget`: 用于外部数据接口（如 AkShare）抓取时的网络交互。
  * `zip` / `unzip`: ETL 流程中处理原始高频压缩包的底层依赖。
* **定时任务**: `crontab` (用于定时触发数据备份与 `optimize.sh` 脚本)。

## 2. ClickHouse 配置依赖 (Database Layer)

基于高性能列式存储的需求，需配置以下组件及参数：

* **ClickHouse Server**: 版本推荐 `22.x` 或更高版本。
* **核心引擎支持**: `MergeTree` 系列引擎（项目核心存储方案）。
* **客户端工具**:
  * `clickhouse-client`: 用于脚本中的 SQL 交互及 Native 管道高速写入。

## 3. Python 核心环境依赖 (Backend & Data Science)

基于 Python 3.10+ 构建，利用向量化算子与多进程框架。

### 3.1 数据科学与向量化引擎

* **`pandas`**: 核心数据结构，用于 ETL 逻辑清洗与中间态处理。
* **`numpy`**: 向量化因子的基础，底层支撑 `Alpha101Engine` 的矩阵运算。
* **`scipy`**: 提供统计学函数支持（如偏度 `skew`、峰度 `kurt` 等因子的计算）。
* **`tqdm`**: 在多进程 ETL 任务中提供进度条监控。

### 3.2 数据库连接驱动

* **`clickhouse-driver`**: Native 协议驱动。用于后台 ETL 的高速写入，支持 TCP 管道。
* **`clickhouse-connect`**: HTTP 协议驱动。推荐用于前端 Streamlit，因其对 Pandas DataFrame 的序列化支持更好，且在 HTTP 长连接下更稳定。
* **`sqlalchemy`**: (可选) 若涉及维度表（如股票信息）的通用映射，可作为 ORM 支持。

### 3.3 并行计算与工具

* **`concurrent.futures`**: 系统内置库，用于 `ProcessPoolExecutor` 实现 28 进程并发清洗。
* **`pyarrow`**: 必需依赖。用于 Stage P1-P5 计算流水线中的 `Parquet` 中间态缓存读取与写入。

## 4. 前端平台依赖 (Frontend Framework)

支撑 Streamlit MPA（多页面应用）架构及交互式可视化。

* **`streamlit`**: 核心前端框架，实现 "Code as Infrastructure"。
* **`plotly`**: 必需。用于绘制交互式 K 线图、涨跌直方图及相似度匹配的走势对比图。
* **`streamlit-aggrid`**: (推荐) 用于在选股器中展示具备排序、筛选功能的高级数据表格。
* **`watchdog`**: 用于开发环境下 Streamlit 页面的实时热更新。

---

## 5. 快速安装指令 (Requirement.txt)

```text
# 基础框架
streamlit
pandas
numpy
scipy

# 数据库驱动
clickhouse-driver
clickhouse-connect

# 数据存储与加速
pyarrow
fastparquet

# 可视化
plotly

# 工具类
tqdm
akshare  # 用于基础行情修补

```
