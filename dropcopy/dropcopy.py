from __future__ import print_function

from abc import abstractmethod
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import logging
import json

import requests

from event.event import TickEvent, FillEvent
from data.price import PriceHandler

class DropcopyHandler(object):
    """
    Provides an abstract base class to handle all dropycopy in the
    backtesting and live trading system.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def stream_to_queue(self):
        """
        Send the manager to the brokerage.
        """
        raise NotImplementedError("Should implement stream_to_queue()")


class OANDAStreamingDropcopy(DropcopyHandler):
    def __init__(
        self, domain, access_token,
        account_id, pairs, events_queue
    ):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.events_queue = events_queue
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.logger = logging.getLogger(__name__)

    def connect_to_stream(self):
        try:
            requests.packages.urllib3.disable_warnings()
            s = requests.Session()
            url = "https://" + self.domain + "/v1/prices"
            headers = {'Authorization' : 'Bearer ' + self.access_token}
            params = {'accountId' : self.account_id}
            req = requests.Request('GET', url, headers=headers, params=params)
            pre = req.prepare()
            resp = s.send(pre, stream=True, verify=False)
            return resp
        except Exception as e:
            s.close()
            print("Caught exception when connecting to stream\n" + str(e))

    def stream_to_queue(self):
        response = self.connect_to_stream()
        if response.status_code != 200:
            return
        for line in response.iter_lines(1):
            if line:
                try:
                    dline = line.decode('utf-8')
                    msg = json.loads(dline)
                except Exception as e:
                    self.logger.error(
                        "Caught exception when converting message into json: %s" % str(e)
                    )
                    return
                if msg['type'] == 'order_fill':
                    self.logger.debug(msg)

                    timestamp = msg['time']
                    ticker = msg['instrument']
                    side = msg['side']
                    quantity = msg['units']
                    price = msg['price']
                    # commission
                    # Create fill event
                    fev = FillEvent(timestamp, ticker,
                                    side, quantity,
                                    price)
                    self.events_queue.put(fev)
