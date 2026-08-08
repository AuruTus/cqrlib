# -*- coding: utf-8 -*-
"""
Created on Thu May  7 11:41:46 2020

@author: Wei_X
"""

import numpy as np
import pandas as pd

p = print


def bband_as_side(data: pd.DataFrame, window: int = 100, width: float = 0.001):
    data["avg"], data["upper"], data["lower"], _ = bband_frac(data=data, window=window, width=width)
    data["side"] = np.nan
    data = side_pick(data=data)

    upper = data[data["upper"] <= data["close"]]  # short signal
    lower = data[data["lower"] >= data["close"]]  # long signal

    p("Bollinger Band results:\n")
    p("Num of times upper limit touched: {0}\nNum of times lower limit touched: {1}".format(upper.shape[0], lower.shape[0]))

    return data.dropna()


def bband_frac(data: pd.DataFrame, window: int = 21, width: float = 0.001):
    """
    Bollinger bands as a fixed fraction of the EMA (price-level form, not a moment).
    Returns (avg, upper, lower, std).
    """
    ewm = data["close"].ewm(span=window)  # single ewm object reused for avg & std
    avg = ewm.mean()
    std = avg * width
    upper, lower = avg + std, avg - std
    return avg, upper, lower, std


def bband_std(data: pd.DataFrame, window: int = 21, width: float = 2.0):
    """
    Bollinger bands as a multiple of the EMA's std (sqrt of the 2nd central moment).
    Returns (avg, upper, lower, std).
    """
    ewm = data["close"].ewm(span=window)  # single ewm object reused for avg & std
    avg = ewm.mean()
    std = ewm.std()
    upper, lower = avg + width * std, avg - width * std
    return avg, upper, lower, std


def side_pick(data: pd.DataFrame):
    """
    Label each bar by the band it touches: -1 upper (short), +1 lower (long).
    """
    for i, idx in enumerate(data.index):
        if data["close"].iloc[i] >= data["upper"].iloc[i]:
            data.loc[idx, "side"] = -1
        elif data["close"].iloc[i] <= data["lower"].iloc[i]:
            data.loc[idx, "side"] = 1
    return data


def get_ma_crossing_signals(
    close: pd.Series, fast_window: int = 5, slow_window: int = 20
) -> pd.Series:
    """
    Dual moving-average crossing signals (for AFML main model output).

    :param close: Close price series.
    :param fast_window: Window of the fast moving average.
    :param slow_window: Window of the slow moving average.
    :return: Series of crossing-event timestamps with the side at each event (1 long / -1 short).
    """
    # 1. Fast and slow moving averages (swap .rolling for .ewm(span=...).mean() to use EMA)
    fast_ma = close.rolling(window=fast_window).mean()
    slow_ma = close.rolling(window=slow_window).mean()

    # 2. Position side by MA comparison
    side = pd.Series(np.nan, index=close.index)
    side[fast_ma > slow_ma] = 1.0  # long regime
    side[fast_ma < slow_ma] = -1.0  # short regime

    # 3. Crossing events: side changed versus the previous bar
    cross_events = side.diff().fillna(0) != 0

    # 4. Keep the side at crossing events only
    signals = side[cross_events].dropna()
    signals.name = "side"

    return signals
