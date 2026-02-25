## WorldQuant Alpha 101 因子定义全集

| 编号 | 公式 (Formula) | 逻辑简述 | 详细说明 |
| --- | --- | --- | --- |
| **alpha_001** | `rank(ts_argmax(signedpower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5` | 极值距离反转 | 关注过去5天内“极端行情”发生的日期距离，越近反转概率越高。 |
| **alpha_002** | `-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)` | 量价背离 | 成交量变化与日内涨幅的相关性，负相关意味着量价背离。 |
| **alpha_003** | `-1 * correlation(rank(open), rank(volume), 10)` | 开盘量价相关 | 高开低走或低开高走与成交量的关系。 |
| **alpha_004** | `-1 * ts_rank(rank(low), 9)` | 低价复合排名 | 低价排名的时序位置，寻找超跌反转。 |
| **alpha_005** | `(rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap)))))` | VWAP偏离度 | 开盘价偏离均线与收盘价偏离均线的复合作用。 |
| **alpha_006** | `-1 * correlation(open, volume, 10)` | 简单开盘量价 | 开盘价与成交量的负相关性。 |
| **alpha_007** | `((adv20 < amount) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : -1)` | 量能确认反转 | 成交额放大（放量）时看反转，缩量时看空(原论文为Volume单位错误，已修正为Amount)。 |
| **alpha_008** | `-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10)))` | 动量差分 | 短期动量与中期动量的差值，捕捉动量衰减。 |
| **alpha_009** | `((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))` | 趋势确认 | 单边行情顺势，震荡行情反转。 |
| **alpha_010** | `rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1)))))` | 趋势确认排名 | Alpha 009 的横截面排名版本。 |
| **alpha_011** | `((rank(ts_max((vwap - close), 3)) + rank(ts_min((vwap - close), 3))) * rank(delta(volume, 3)))` | 量价偏离极值 | VWAP偏离度的极值与成交量变化的结合。 |
| **alpha_012** | `(sign(delta(volume, 1)) * (-1 * delta(close, 1)))` | 简单量价反转 | 缩量跌或放量涨时为正，反之为负。 |
| **alpha_013** | `-1 * rank(covariance(rank(close), rank(volume), 5))` | 量价协方差 | 价格与成交量的协方差排名。 |
| **alpha_014** | `((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10))` | 二阶动量与量价 | 收益率加速度与开盘量价相关性的结合。 |
| **alpha_015** | `-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)` | 高点量价动量 | 最高价与成交量相关性的短期动量。 |
| **alpha_016** | `-1 * rank(covariance(rank(high), rank(volume), 5))` | 高点量价协方差 | 类似Alpha13，但使用最高价。 |
| **alpha_017** | `(((-1 * rank(ts_rank(close, 10))) * rank(delta(delta(close, 1), 1))) * rank(ts_rank((volume / adv20), 5)))` | 主力吸筹复合 | 价格位置、加速度、放量程度的复合排名。 |
| **alpha_018** | `-1 * rank(((stddev(abs((close - open)), 5) + (close - open)) + correlation(close, open, 10)))` | 日内波动综合 | 波动率、日内涨跌、收开相关性的综合。 |
| **alpha_019** | `((-1 * sign(((close - delay(close, 7)) + delta(close, 7)))) * (1 + rank((1 + sum(returns, 250)))))` | 长期动量修正 | 基于年线回报率修正的短期反转。 |
| **alpha_020** | `(((-1 * rank((open - delay(high, 1)))) * rank((open - delay(close, 1)))) * rank((open - delay(low, 1))))` | 跳空缺口 | 衡量开盘价相对于昨日高、低、收的位置。 |
| **alpha_021** | `((mean(close, 8) + stddev(close, 8)) < mean(close, 2)) ? -1 : ((mean(close, 2) < (mean(close, 8) - stddev(close, 8))) ? 1 : ((amount / adv20 < 1) ? -1 : 1))` | 布林带趋势 | 短期均价突破布林带看反转，否则看量（已修正为Amount缩量看空）。 |
| **alpha_022** | `-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20)))` | 量价相关性变动 | 量价相关性剧烈变动且波动率高时看空。 |
| **alpha_023** | `((mean(high, 20) < high) ? (-1 * delta(high, 2)) : 0)` | 高点突破反转 | 创新高后看空短期高点变化。 |
| **alpha_024** | `((((delta(mean(close, 100), 100) / delay(close, 100)) < 0.05) \|\| ((delta(mean(close, 100), 100) / delay(close, 100)) == 0.05)) ? (-1 * (close - ts_min(close, 100))) : (-1 * delta(close, 3)))`| 长期均线盘整突破 | 百日均线变化率极低（盘整）时做空乖离，否则做空动量。|
| **alpha_025** | `rank(((((-1 * returns) * adv20) * vwap) * (high - close)))` | 价量复合因子 | 结合反转、流动性和日内强度的复合排序。 |
| **alpha_026** | `-1 * ts_max(correlation(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)` | 高点量能时序相关 | 寻找过去3天内量价时序配合度最高的时刻。 |
| **alpha_027** | `((0.5 < rank((sum(correlation(rank(volume), rank(vwap), 6), 2) / 2.0))) ? -1 : 1)` | 量价排名背离 | 成交量与均价排名的相关性过高时看空。 |
| **alpha_028** | `scale(((correlation(adv20, low, 5) + ((high + low) / 2)) - close))` | 低点放量与位置 | 流动性与低点相关性，叠加收盘价位置。 |
| **alpha_029** | `(ts_min(rank(rank(scale(log(ts_min(rank(rank((-1 * rank(delta((close - 1), 5))))), 2))))), 5) + ts_rank(delay((-1 * returns), 6), 5))` | 深度嵌套反转 | 极度复杂的递归反转因子，结合了动量延迟。 |
| **alpha_030** | `(((1.0 - rank(((sign(delta(close, 1)) + sign(delay(delta(close, 1), 1))) + sign(delay(delta(close, 1), 2))))) * sum(volume, 5)) / sum(volume, 20))` | 连涨连跌反转 | 连续涨跌信号的反向排名，并用短期/长期成交量比率加权。 |
| **alpha_031** | `((rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3)))) + sign(scale(correlation(adv20, low, 12))))` | 复合动量反转 | 结合价格变动衰减、短期反转及流动性低点相关性。 |
| **alpha_032** | `(scale(((sum(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230))))` | 均值回归+VWAP | 收盘价相对7日均线偏离 + VWAP与滞后收盘价相关性。 |
| **alpha_033** | `rank((-1 * (1 - (open / close))))` | 日内反转 | 日内跌幅越大，得分越高（看多反转）。 |
| **alpha_034** | `rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))` | 波动率收缩 | 收益率波动率收缩且价格下跌时看多。 |
| **alpha_035** | `((ts_rank(volume, 32) * (1 - ts_rank(((close + high) - low), 16))) * (1 - ts_rank(returns, 32)))` | 量价配合反转 | 成交量高、振幅小、收益率低时的反转组合。 |
| **alpha_036** | `(((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) + (0.73 * rank(ts_rank(delay((-1 * returns), 6), 5)))) + rank(abs(correlation(vwap, adv20, 6)))) + (0.6 * rank((((sum(close, 200) / 200) - open) * (close - open)))))` | 超级复合因子 | 量价相关性、日内涨跌、动量反转、VWAP相关性等5合1。 |
| **alpha_037** | `(rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))` | 实体长期相关 | 昨日实体与今日收盘价的长期相关性。 |
| **alpha_038** | `((-1 * rank(ts_rank(close, 10))) * rank((close / open)))` | 高位日内反转 | 价格处于高位且日内上涨时看空。 |
| **alpha_039** | `((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sum(returns, 250))))` | 量能衰减反转 | 成交量衰减背景下的动量反转。 |
| **alpha_040** | `((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))` | 高点波动量价 | 高点波动率高且与成交量正相关时看空。 |
| **alpha_041** | `(((high * low)^0.5) - vwap)` | 几何均价偏离 | 最高最低几何平均价与VWAP的差值。 |
| **alpha_042** | `(rank((vwap - close)) / rank((vwap + close)))` | VWAP相对强弱 | VWAP与收盘价差值的相对排名比率。 |
| **alpha_043** | `(ts_rank((amount / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8))` | 放量下跌 | 成交额放大且价格下跌时得分高(原论文 Volume 单位错，已修正为 Amount)。 |
| **alpha_044** | `(-1 * correlation(high, rank(volume), 5))` | 高点成交量相关 | 最高价与成交量排名的负相关性。 |
| **alpha_045** | `((-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) * rank(correlation(sum(close, 5), sum(close, 20), 2)))))` | 均线与量价复合 | 长期均线位置、量价相关性、价格动量相关性的复合。 |
| **alpha_046** | `((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ? -1 : (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < 0) ? 1 : ((-1 * 1) * (close - delay(close, 1)))))` | 均线乖离策略 | 基于10日均线乖离率的均值回归策略。 |
| **alpha_047** | `((((rank((1 / close)) * (amount / adv20)) * (high * rank((high - close)))) / (sum(high, 5) / 5)) - rank((vwap - delay(vwap, 5))))` | 价格倒数与动量 | 结合低价股效应、放量程度和VWAP动量(已修正量纲)。 |
| **alpha_048** | `(indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) * delta(close, 1)) / close), IndClass.subindustry) / sum(((delta(close, 1) / delay(close, 1))^2), 250))` | 行业中性自相关 | 收益率自相关性经行业中性化后的标准化值。 |
| **alpha_049** | `(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.1)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))` | 超跌反转 | 均线乖离率极低时看多，否则做空短期反转。 |
| **alpha_050** | `(-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5))` | 量价背离极值 | 成交量与VWAP排名正相关的最大值取反。 |
| **alpha_051** | `(((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ? 1 : ((-1 * 1) * (close - delay(close, 1))))` | 均线乖离反转 | 同Alpha 49，但阈值更宽松。 |
| **alpha_052** | `((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) - sum(returns, 20)) / 220))) * ts_rank(volume, 5))` | 低点反转与长期动量 | 低点抬升、长期动量强、成交量大的组合。 |
| **alpha_053** | `(-1 * delta((((close - low) - (high - close)) / (close - low)), 9))` | K线形态变化 | 收盘价在K线内部位置的变化率（类似IBS变化）。 |
| **alpha_054** | `((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))` | K线结构因子 | 基于开收高低价的复杂非线性组合。 |
| **alpha_055** | `(-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volume), 6))` | 价格位置与量相关 | 价格在近期区间的位置(Stoch)与成交量的负相关。 |
| **alpha_056** | `(0 - (1 * (rank((sum(returns, 10) / sum(sum(returns, 2), 3))) * rank((returns * cap)))))` | 动量与市值 | 短期动量强度与市值加权收益的负向结合。 |
| **alpha_057** | `(0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))))` | VWAP偏离衰减 | 收盘价偏离VWAP，除以极值发生时间的衰减。 |
| **alpha_058** | `(-1 * ts_rank(decay_linear(correlation(indneutralize(vwap, IndClass.sector), volume, 3), 7), 5))` | 行业中性量价衰减 | 行业中性化VWAP与成交量相关性的线性衰减排名（取整周期）。 |
| **alpha_059** | `(-1 * ts_rank(decay_linear(correlation(indneutralize(vwap, IndClass.industry), volume, 4), 16), 8))` | 行业中性量价衰减2 | 同Alpha 58，但参数周期不同(已移除冗余结构)。 |
| **alpha_060** | `(0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(rank(ts_argmax(close, 10))))))` | K线形态与极值 | IBS形态变体与价格极值位置的差值。 |
| **alpha_061** | `((rank((vwap - ts_min(vwap, 16))) < rank(correlation(vwap, adv180, 17))) ? 1 : 0)` | VWAP位置与流动性 | VWAP近期位置与VWAP-成交额相关性的比较。 |
| **alpha_062** | `((rank(correlation(vwap, sum(adv20, 22), 9)) < rank(((rank(open) * 2) < (rank(((high + low) / 2)) + rank(high))))) ? -1 : 0)` | VWAP量价与K线 | VWAP量价相关性与K线形态排名的比较。 |
| **alpha_063** | `((rank(decay_linear(delta(indneutralize(close, IndClass.industry), 2), 8)) - rank(decay_linear(correlation(vwap, sum(adv180, 37), 13), 12))) * -1)` | 中性化动量衰减 | 行业中性化价格动量衰减与加权价格流动性相关性的差(移除冗余)。 |
| **alpha_064** | `((rank(correlation(sum(open, 12), sum(adv120, 12), 16)) < rank(delta(((high + low) / 2), 3))) ? -1 : 0)` | 加权价格动量 | 加权价格与流动性相关性与另一加权价格动量的比较(移除冗余)。 |
| **alpha_065** | `((rank(correlation(open, sum(adv60, 8), 6)) < rank((open - ts_min(open, 13)))) ? -1 : 0)` | 加权价格与开盘 | 加权价格与流动性相关性与开盘价位置的比较(移除冗余)。 |
| **alpha_066** | `((rank(decay_linear(delta(vwap, 3), 7)) + ts_rank(decay_linear((((low - vwap) / (open - ((high + low) / 2)))), 11), 6)) * -1)` | VWAP动量与IBS | VWAP动量衰减与IBS形态时序排名的结合(移除Low*冗余)。 |
| **alpha_067** | `((rank((high - ts_min(high, 2)))^rank(correlation(indneutralize(vwap, IndClass.sector), indneutralize(adv20, IndClass.subindustry), 6))) * -1)` | 高点位置与量价 | 高点位置的幂次，指数为行业中性量价相关性。 |
| **alpha_068** | `((ts_rank(correlation(rank(high), rank(adv15), 8), 13) < rank(delta(close, 1))) ? -1 : 0)` | 高点流动性与动量 | 高点与流动性相关性的时序排名与加权价格动量的比较(移除冗余)。 |
| **alpha_069** | `((rank(ts_max(delta(indneutralize(vwap, IndClass.industry), 2), 4))^ts_rank(correlation(close, adv20, 4), 9)) * -1)` | 中性化VWAP突破 | 行业中性化 VWAP 突变与加权价格流动性相关性的幂次组合(移除冗余)。 |
| **alpha_070** | `((rank(delta(vwap, 1))^ts_rank(correlation(indneutralize(close, IndClass.industry), adv50, 17), 17)) * -1)` | VWAP动量与中性 | VWAP动量与行业中性收盘价流动性相关性的幂次组合。 |
| **alpha_071** | `max(ts_rank(decay_linear(correlation(ts_rank(close, 3), ts_rank(adv180, 12), 18), 4), 15), ts_rank(decay_linear((rank(((low + open) - (2 * vwap)))^2), 16), 4))` | 动量与K线形态 | 价格动量-流动性相关性与K线形态偏离度的最大值。 |
| **alpha_072** | `(rank(decay_linear(correlation(((high + low) / 2), adv40, 8), 10)) / rank(decay_linear(correlation(ts_rank(vwap, 3), ts_rank(volume, 18), 6), 2)))` | 均价流动性比率 | 均价-流动性相关性与 VWAP-成交量相关性的比率。 |
| **alpha_073** | `(max(rank(decay_linear(delta(vwap, 4), 2)), ts_rank(decay_linear(((-1 * delta(open, 2)) / open), 3), 16)) * -1)` | VWAP反转与动量 | VWAP动量衰减与加权价格反转的最大值(移除冗余)。 |
| **alpha_074** | `((rank(correlation(close, sum(adv30, 37), 15)) < rank(correlation(rank(((high * 0.0261661) + (vwap * (1 - 0.0261661)))), rank(volume), 11))) ? -1 : 0)` | 收盘流动性相关 | 收盘价-流动性相关性与加权价格-成交量相关性的比较。 |
| **alpha_075** | `((rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12))) ? 1 : 0)` | VWAP量价与低点 | VWAP-成交量相关性与低点-流动性相关性的比较。 |
| **alpha_076** | `(max(rank(decay_linear(delta(vwap, 1), 11)), ts_rank(decay_linear(ts_rank(correlation(indneutralize(low, IndClass.sector), adv81, 8), 19), 17), 19)) * -1)` | VWAP动量与低点 | VWAP动量衰减与行业中性化低点-流动性相关性的最大值。 |
| **alpha_077** | `min(rank(decay_linear((((high + low) / 2) - vwap), 20)), rank(decay_linear(correlation(((high + low) / 2), adv40, 3), 5)))` | 均价偏离与相关 | 均价-VWAP偏离衰减与均价-流动性相关性衰减的最小值(移除H-H冗余)。 |
| **alpha_078** | `(rank(correlation(sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 19), sum(adv40, 19), 6))^rank(correlation(rank(vwap), rank(volume), 5)))` | 加权价格流动性 | 加权价格-流动性相关性的幂次，指数为 VWAP-成交量相关性。 |
| **alpha_079** | `((rank(delta(indneutralize(((close * 0.60733) + (open * (1 - 0.60733))), IndClass.sector), 1)) < rank(correlation(ts_rank(vwap, 3), ts_rank(adv150, 9), 14))) ? 1 : 0)` | 中性化价格动量 | 行业中性化加权价格动量与 VWAP-流动性相关性的比较。 |
| **alpha_080** | `((rank(sign(delta(indneutralize(((open * 0.868128) + (high * (1 - 0.868128))), IndClass.industry), 4)))^ts_rank(correlation(high, adv10, 5), 5)) * -1)` | 中性化价格突变 | 行业中性化价格突变符号与高点-流动性相关性的幂次组合。 |
| **alpha_081** | `((rank(log(product(rank((rank(correlation(vwap, sum(adv10, 49), 8))^4)), 14))) < rank(correlation(rank(vwap), rank(volume), 5))) ? -1 : 0)` | VWAP流动性复合 | VWAP-流动性相关性的高阶矩与 VWAP-成交量相关性的比较。 |
| **alpha_082** | `(min(rank(decay_linear(delta(open, 1), 14)), ts_rank(decay_linear(correlation(indneutralize(volume, IndClass.sector), open, 17), 6), 13)) * -1)` | 开盘动量与量价 | 开盘价动量衰减与行业中性成交量-开盘价相关性的最小值(移除Open*冗余)。 |
| **alpha_083** | `((rank(delay(((high - low) / (sum(close, 5) / 5)), 2)) * rank(rank(volume))) / (((high - low) / (sum(close, 5) / 5)) / ((vwap - close) + 0.001)))` | K线形态与量价 | 滞后K线实体比例与成交量排名的乘积，除以 VWAP-Close价差(加微小值防除零)。 |
| **alpha_084** | `signedpower(ts_rank((vwap - ts_max(vwap, 15)), 20), delta(close, 4))` | VWAP位置与动量 | VWAP位置时序排名的幂次，指数为收盘价动量。 |
| **alpha_085** | `(rank(correlation(((high * 0.876703) + (close * (1 - 0.876703))), adv30, 9))^rank(correlation(ts_rank(((high + low) / 2), 3), ts_rank(volume, 10), 7)))` | 加权价格与均价 | 加权价格-流动性相关性的幂次，指数为均价-成交量相关性。 |
| **alpha_086** | `((ts_rank(correlation(close, sum(adv20, 14), 6), 20) < rank((close - vwap))) ? -1 : 0)` | 收盘流动性与偏离 | 收盘价-流动性相关性时序排名与收盘价-VWAP 偏离排名的比较(移除冗余)。 |
| **alpha_087** | `(max(rank(decay_linear(delta(((close * 0.369701) + (vwap * (1 - 0.369701))), 1), 2)), ts_rank(decay_linear(abs(correlation(indneutralize(adv81, IndClass.industry), close, 13)), 4), 14)) * -1)` | 加权价格与中性 | 加权价格动量衰减与行业中性流动性-收盘价相关性的最大值。 |
| **alpha_088** | `min(rank(decay_linear((((rank(open) + rank(low)) - rank(high)) - rank(close)), 8)), ts_rank(decay_linear(correlation(ts_rank(close, 8), ts_rank(adv60, 20), 8), 6), 2))` | K线综合与动量 | K线四价排名的线性衰减与收盘价-流动性相关性的最小值。 |
| **alpha_089** | `(ts_rank(decay_linear(correlation(low, adv10, 6), 5), 3) - ts_rank(decay_linear(delta(indneutralize(vwap, IndClass.industry), 3), 10), 15))` | 低点流动性与中性 | 低点-流动性相关性与行业中性 VWAP 动量的差值(移除Low*冗余)。 |
| **alpha_090** | `((rank((close - ts_max(close, 4)))^ts_rank(correlation(indneutralize(adv40, IndClass.subindustry), low, 5), 3)) * -1)` | 高位回撤与中性 | 收盘价回撤排名与行业中性流动性-低点相关性的幂次组合。 |
| **alpha_091** | `((ts_rank(decay_linear(decay_linear(correlation(indneutralize(close, IndClass.industry), volume, 9), 16), 3), 4) - rank(decay_linear(correlation(vwap, adv30, 4), 2))) * -1)` | 中性化价格与VWAP | 行业中性化价格-成交量相关性与 VWAP-流动性相关性的差值。 |
| **alpha_092** | `min(ts_rank(decay_linear(((((high + low) / 2) + close) < (low + open)), 14), 18), ts_rank(decay_linear(correlation(rank(low), rank(adv30), 7), 6), 6))` | K线形态与低点 | K线形态条件的衰减排名与低点-流动性相关性的最小值。 |
| **alpha_093** | `(ts_rank(decay_linear(correlation(indneutralize(vwap, IndClass.industry), adv81, 17), 19), 7) / rank(decay_linear(delta(((close * 0.524434) + (vwap * (1 - 0.524434))), 2), 16)))` | 中性化VWAP与价格 | 行业中性化 VWAP-流动性相关性除以加权价格动量。 |
| **alpha_094** | `((rank((vwap - ts_min(vwap, 11)))^ts_rank(correlation(ts_rank(vwap, 19), ts_rank(adv60, 4), 18), 2)) * -1)` | VWAP位置与相关 | VWAP位置排名的幂次，指数为 VWAP-流动性相关性的时序排名。 |
| **alpha_095** | `((rank((open - ts_min(open, 12))) < ts_rank((rank(correlation(sum(((high + low) / 2), 19), sum(adv40, 19), 12))^5), 11)) ? 1 : 0)` | 开盘位置与均价 | 开盘价位置排名与均价-流动性相关性的比较。 |
| **alpha_096** | `(max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 3), 4), 8), ts_rank(decay_linear(ts_argmax(correlation(ts_rank(close, 7), ts_rank(adv60, 4), 3), 12), 14), 13)) * -1)` | VWAP量价与收盘 | VWAP-成交量相关性与收盘价-流动性相关性极值的最大值。 |
| **alpha_097** | `((rank(decay_linear(delta(indneutralize(((low * 0.721001) + (vwap * (1 - 0.721001))), IndClass.industry), 3), 20)) - ts_rank(decay_linear(ts_rank(correlation(ts_rank(low, 7), ts_rank(adv60, 17), 4), 18), 15), 6)) * -1)` | 加权价格与低点 | 行业中性化加权价格动量与低点-流动性相关性的差值。 |
| **alpha_098** | `(rank(decay_linear(correlation(vwap, sum(adv5, 26), 4), 7)) - rank(decay_linear(ts_rank(ts_argmin(correlation(rank(open), rank(adv15), 20), 8), 6), 8)))` | VWAP流动性与开盘 | VWAP-流动性相关性与开盘价-流动性相关性极值的差值。 |
| **alpha_099** | `((rank(correlation(sum(((high + low) / 2), 19), sum(adv60, 19), 8)) < rank(correlation(low, volume, 6))) ? -1 : 0)` | 均价流动性与低点 | 均价-流动性相关性与低点-成交量相关性的比较。 |
| **alpha_100** | `(-1 * (((1.5 * scale(indneutralize(indneutralize(rank(((((close - low) - (high - close)) / (high - low)) * volume)), IndClass.subindustry), IndClass.subindustry))) - scale(indneutralize((correlation(close, rank(adv20), 5) - rank(ts_argmin(close, 30))), IndClass.subindustry))) * (amount / adv20)))` | 中性化量价与K线 | 行业中性化量价排名与收盘价相关性的差值，经成交额加权(修正量纲)。 |
| **alpha_101** | `((close - open) / ((high - low) + 0.001))` | Alpha 101 | 经典的 K 线实体/振幅比率。 |