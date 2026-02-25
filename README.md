# Quantitative database and visualization platform

本项目使用clickhouse搭建量化研究中海量金融行情数据和三秒级买卖盘数据存储的数据库，以及各类因子计算结果数据库。并使用Python开发可视化交互平台。系统遵循 **“Thin Application, Thick Database”** 的设计原则，构建了以 ClickHouse 为核心的“三库一平台”量化研究基础设施。

## 🛠 系统核心架构

本项目由三个底层数据库及一个前端交互平台四部分组成：

1. **`stock_3tick_db` (三秒极买卖盘数据库)**：存储 3 秒级 L2 买卖盘数据。
2. **`quant_db` (日线行情仓库)**：提供日线级标准化行情、基本面估值及另类情绪数据。
3. **`factor_db` (因子特征集市)**：集成技术、动量、价值及 Alpha101 因子。
4. **Quantlib (量化分析平台)**：基于 Streamlit 构建，通过 SQL 计算下推技术数据的可视化。


## 📂 项目目录结构

* `app`文件夹下存放前端平台代码
* `database`文件夹下存放数据库建表语句、因子计算公式、数据库结构内容概览
* 项目的完整设计细节请查阅 `Project report.md`

## 🚦 快速开始

#### 环境要求

* **Linux**: Ubuntu 20.04+
* **ClickHouse**: 22.x+
* **Python**: 3.10+ 
* (依赖清单详见 `requirements.md`)

#### 启动平台

```bash
cd app/Quantlib
streamlit run main.py
```

## 📊 可视化展示

本项目提供了直观的网页版可视化成果，可点击以下文件直接查阅：

* **量化数据库结构**: `database/量化数据库可视化网页.html`
* **前端平台交互**: `app/量化前端平台可视化网页.html`
