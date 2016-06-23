def get_tick_size(instrument):
    _dict = {'EURUSD': 0.0001,
             'FESXXX': 1}
    return _dict.get(instrument, 0.0001)
