import numpy as np
import pandas as pd
from scipy.stats import rankdata

class Alpha101Engine:
    """
    Alpha 101 Quantitative Factor Computation Engine.
    
    Implementation based on WorldQuant's "101 Formulaic Alphas" using NumPy 
    and Pandas for vectorized time-series and cross-sectional operations.
    """

    # --------------------------------------------------------------------------
    # Time-Series Operators (Temporal Operations)
    # --------------------------------------------------------------------------

    @staticmethod
    def delay(series: pd.Series, period: int) -> pd.Series:
        """Lag operator: Shifts the series back by a specified period."""
        return series.shift(period)

    @staticmethod
    def delta(series: pd.Series, period: int) -> pd.Series:
        """Difference operator: Calculates x_t - x_{t-n}."""
        return series.diff(period)

    @staticmethod
    def correlation(x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """Rolling Correlation: Computes Pearson correlation coefficient over a sliding window."""
        return x.rolling(window=window).corr(y)

    @staticmethod
    def covariance(x: pd.Series, y: pd.Series, window: int) -> pd.Series:
        """Rolling Covariance: Computes the covariance between two series over a sliding window."""
        return x.rolling(window=window).cov(y)

    @staticmethod
    def ts_min(series: pd.Series, window: int) -> pd.Series:
        """Rolling Minimum: Returns the minimum value within a sliding window."""
        return series.rolling(window=window).min()

    @staticmethod
    def ts_max(series: pd.Series, window: int) -> pd.Series:
        """Rolling Maximum: Returns the maximum value within a sliding window."""
        return series.rolling(window=window).max()

    @staticmethod
    def ts_argmax(series: pd.Series, window: int) -> pd.Series:
        """Temporal Argmax: Returns the relative index of the maximum value within the window."""
        return series.rolling(window).apply(lambda x: float(np.argmax(x)), raw=True)

    @staticmethod
    def ts_argmin(series: pd.Series, window: int) -> pd.Series:
        """Temporal Argmin: Returns the relative index of the minimum value within the window."""
        return series.rolling(window).apply(lambda x: float(np.argmin(x)), raw=True)

    @staticmethod
    def ts_rank(series: pd.Series, window: int) -> pd.Series:
        """Rolling Rank: Computes the percentile rank of the current value within a sliding window."""
        def _rank_last(arr):
            return rankdata(arr)[-1]
        return series.rolling(window).apply(_rank_last, raw=True)

    @staticmethod
    def sum(series: pd.Series, window: int) -> pd.Series:
        """Rolling Sum: Computes the sum of values over a sliding window."""
        return series.rolling(window).sum()

    @staticmethod
    def product(series: pd.Series, window: int) -> pd.Series:
        """Rolling Product: Computes the geometric product using log-transformation for numerical stability."""
        return np.exp(np.log(series).rolling(window).sum())

    @staticmethod
    def stddev(series: pd.Series, window: int) -> pd.Series:
        """Rolling Standard Deviation: Computes the volatility over a sliding window."""
        return series.rolling(window).std()

    @staticmethod
    def decay_linear(series: pd.Series, window: int) -> pd.Series:
        """Linear Decay Weighted Moving Average: Computes LWMA with weights 1 to d."""
        weights = np.arange(1, window + 1)
        w_sum = weights.sum()
        return series.rolling(window).apply(lambda x: np.dot(x, weights) / w_sum, raw=True)

    # --------------------------------------------------------------------------
    # Cross-Sectional Operators (Spatial Operations)
    # --------------------------------------------------------------------------

    @staticmethod
    def rank(series: pd.Series) -> pd.Series:
        """Cross-Sectional Rank: Normalizes the series into percentile ranks [0, 1]."""
        return series.rank(pct=True)

    @staticmethod
    def scale(series: pd.Series, target: float = 1.0) -> pd.Series:
        """Rescaling Operator: Rescales the series such that sum(abs(x)) equals the target value."""
        return series.mul(target).div(np.abs(series).sum())

    # --------------------------------------------------------------------------
    # Mathematical and Logical Operators
    # --------------------------------------------------------------------------

    @staticmethod
    def signedpower(series: pd.Series, exponent: float) -> pd.Series:
        """Signed Power: Computes sign(x) * |x|^a to preserve the direction of the signal."""
        return np.sign(series) * (np.abs(series) ** exponent)

    @staticmethod
    def if_else(condition: pd.Series, x: pd.Series, y: pd.Series) -> pd.Series:
        """Element-wise Conditional: Returns x if condition is true, otherwise y."""
        return np.where(condition, x, y)