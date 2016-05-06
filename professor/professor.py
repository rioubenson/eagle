from analysis import Brain

class Professor(object):
    '''A class that attempts to find '''
    def __init__(self, instrument, time_frame, type):
        self.instrument = instrument
        self.time_frame = time_frame
        self.type = type(instrument, time_frame)

    def start_professor(self):
        results = self.type.start()

        # print results

if __name__ == "__main__":
    # Trade on GBP/USD and EUR/USD
    pair = "EURUSD"
    time_frame = '1M'
    type = Brain
    professor = Professor(pair, time_frame, type)
    professor.start_professor()
