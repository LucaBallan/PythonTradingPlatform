import numpy
import datetime
import threading
from collections import deque
from TradeInterface import current_time


#
#
#
class QuoteServer(threading.Thread):
    __mutex = None
    __exiting = None
    __quote_db = None
    __mutex_listeners = None
    __listeners = None
    __maxlen = 60 * 60 * 6
    #
    __trade = None
    #
    time_frequency_sec = None

    #
    #
    #
    def __init__(self, trade):
        super().__init__()
        self.setName('QuoteServer')

        #
        self.__mutex = threading.Lock()
        self.__exiting = threading.Event()
        self.__quote_db = dict()
        self.__mutex_listeners = threading.Lock()
        self.__listeners = set()
        #
        self.__trade = trade
        #
        self.time_frequency_sec = 1.0

    #
    #
    #
    def run(self):
        next_time = current_time()
        while True:
            #
            # wait and check exiting
            #
            time_diff = current_time() - next_time
            second_left = self.time_frequency_sec - (time_diff.seconds + (time_diff.microseconds / (1000.0*1000.0)))
            if second_left < 0.0:
                print('lost ticker: reset')
                second_left = 0.0
                next_time = current_time()
            else:
                next_time = next_time + datetime.timedelta(milliseconds=self.time_frequency_sec * 1000.0)
            if self.__exiting.wait(second_left):
                break

            #
            # Start
            #
            self.__mutex.acquire()
            symbols = [symbol for symbol in self.__quote_db]
            if len(symbols) != 0:
                try:
                    quote = self.__trade.get_quote(symbols, intraday=True)
                    ask_time = current_time()
                    for q in quote:
                        if q[0] in self.__quote_db:
                            self.__quote_db[q[0]][1].append([(float(q[1]['bid']) + float(q[1]['ask'])) / 2.0,  ask_time])
                except Exception as e:
                    print('QuoteServer: ' + str(e))  # TODO HANDLE CONNECTION LOST!!! WITH QUIT!!! or retry
            #
            # End
            #
            self.__mutex.release()

            #
            # Wake up consumers
            #
            self.__mutex_listeners.acquire()
            for data_ready_flags in self.__listeners:
                data_ready_flags.set()
            self.__mutex_listeners.release()

        #
        #
        #
        print('QuoteServer stopped.')

    #
    #
    #
    def add_listener(self):
        t = threading.Event()
        self.__mutex_listeners.acquire()
        self.__listeners.add(t)
        self.__mutex_listeners.release()
        return t

    #
    #
    #
    def remove_listener(self, t):
        self.__mutex_listeners.acquire()
        self.__listeners.remove(t)
        self.__mutex_listeners.release()

    #
    #
    #
    def add_quote(self, symbol):
        symbol = symbol.strip().upper()
        self.__mutex.acquire()
        if symbol not in self.__quote_db:
            self.__quote_db[symbol] = [1, deque(maxlen=self.__maxlen)]
        else:
            self.__quote_db[symbol][0] += 1
        self.__mutex.release()

    #
    #
    #
    def remove_quote(self, symbol):
        symbol = symbol.strip().upper()
        self.__mutex.acquire()
        if symbol in self.__quote_db:
            self.__quote_db[symbol][0] -= 1
            if self.__quote_db[symbol][0] <= 0:
                self.__quote_db.pop(symbol)
        self.__mutex.release()

    #
    #
    #
    def list_quote(self):
        self.__mutex.acquire()
        list_quote = [x.ljust(6) + ' -> ' + str(self.__quote_db[x][0]) for x in self.__quote_db]
        self.__mutex.release()
        return list_quote

    #
    #
    #
    def get_quote(self, symbol, all_data):
        if symbol not in self.__quote_db:
            return None, None

        self.__mutex.acquire()
        database = self.__quote_db[symbol][1]
        if len(database) == 0:
            self.__mutex.release()
            return [], numpy.array([])
        if all_data:
            data_x = [database[j][1] for j in range(len(database))]
            data_y = numpy.array([database[j][0] for j in range(len(database))])
        else:
            data_x = [database[-1][1]]
            data_y = numpy.array([database[-1][0]])
        self.__mutex.release()
        return data_x, data_y

    #
    #
    #
    def quit(self):
        self.__mutex.acquire()
        self.__exiting.set()
        self.__mutex.release()
