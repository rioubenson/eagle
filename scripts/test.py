# Get data then
import os

import pandas as pd

from common.bars import ticks_to_candle
from data.price import HistoricCSVPriceHandler
from indicator.indicator import ROC
from settings import CSV_DATA_DIR
pair_path = os.path.join(CSV_DATA_DIR, '%s_%s.csv' % ('EURUSD', '20160601'))
data = pd.io.parsers.read_csv(
    pair_path, header=0, index_col=0,
    parse_dates=True, dayfirst=True,
    names=("Time", "Ask", "Bid", "AskVolume", "BidVolume")
)

bars = ticks_to_candle(data, '1Min', 'Ask')
bars = ROC(bars, 9)
print data
bars.to_csv(os.path.join(CSV_DATA_DIR, '%s_%s_bars_1m.csv' % ('EURUSD', '20160601')))