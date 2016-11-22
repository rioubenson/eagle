from decimal import Decimal
import os


ENVIRONMENTS = { 
    "streaming": {
        #"real": "stream-fxtrade.oanda.com",
        #"practice": "stream-fxpractice.oanda.com",
        "sandbox": "stream-sandbox.oanda.com"
    },
    "api": {
        #"real": "api-fxtrade.oanda.com",
        #"practice": "api-fxpractice.oanda.com",
        "sandbox": "api-sandbox.oanda.com"
    }
}

CSV_DATA_DIR = "C:/Users/Riou/PycharmProjects/eagle/real_data/BRN"  #'C:/Users/Riou/PycharmProjects/eagle/real_data/EURUSD' #' / apps / homefs1 / rbenson / eagle / '  #'os.environ.get('EAGLE_CSV_DATA_DIR', None)
OUTPUT_RESULTS_DIR ='C:/Users/Riou/PycharmProjects/eagle' #'C:\Users\Riou\Eagle' #'/apps/homefs1/rbenson/eagle/' #os.environ.get('EAGLE_OUTPUT_RESULTS_DIR', None)
OUTPUT_DIR = 'C:/Users/Riou/PycharmProjects/eagle'

DOMAIN = "sandbox"
STREAM_DOMAIN = ENVIRONMENTS["streaming"][DOMAIN]
API_DOMAIN = ENVIRONMENTS["api"][DOMAIN]
ACCESS_TOKEN = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
ACCOUNT_ID = os.environ.get('OANDA_API_ACCOUNT_ID', None)

BASE_CURRENCY = "GBP"
EQUITY = Decimal("1000000.00")


TRADING_PARAMETERS = {
    'GRIDIRON': {
        "EURUSD": {
            'equity': 0.1,
            'grid_spacing': 2,
            },
        "BRENTX": {
            'equity': 0.001,
            'grid_spacing': 20,
        }
    }

}