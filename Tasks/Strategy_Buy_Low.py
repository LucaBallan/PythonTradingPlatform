import datetime
from typing import Optional

from Tasks.FollowSymbolTask import FollowSymbolTask
from TradeInterface import datetime_delay


#
#
#
class SellTrailing(FollowSymbolTask):
    __order_data = None

    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)
        if state is not None:
            self.__order_data = state['__order_data']
        else:
            self.__order_data = dict()

    def set_order_data(self, symbol, qty, margin, order_term, prev_order_id, update_freq):
        self.symbol = symbol
        self.__order_data['quantity'] = qty
        self.__order_data['margin'] = margin
        self.__order_data['order_term'] = order_term
        self.__order_data['prev_order_id'] = prev_order_id
        self.__order_data['update_freq'] = update_freq

    def __str__(self) -> str:
        return super().__str__() + '  ' + 'SELL'.ljust(9) + ' ' + self.symbol.ljust(5) + ' margin = ' + str(self.__order_data['margin'] * 100.0) + '%' + '  qty = ' + str(self.__order_data['quantity'])

    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['__order_data'] = self.__order_data
        return c_state

    def __sell_order(self, data, limit_price, kill_if_succeed):
        trade = data['trade']
        limit_price = round(limit_price, 2)

        try:
            # order_no, msg = trade.place_limit_order(action='SELL', symbol=self.symbol, quantity=self.__order_data['quantity'], limit_price=limit_price, order_term=self.__order_data['order_term'], prev_order_id=self.__order_data['prev_order_id'], session=market_session())
            # TODO
            msg = 'limit_price = ' + str(limit_price) + '   '
            order_no = 0
            # TODO
        except ValueError as e:
            # abort
            return True, [], str(e), None
        if order_no is None:
            # abort
            return True, [], 'trade returned None', None

        # save order
        self.__order_data['order_no'] = order_no

        # order sent
        if kill_if_succeed:
            # Kill
            return True, [], msg + ' order_no = ' + str(order_no), None
        else:
            # Continue
            return False, [], msg + ' order_no = ' + str(order_no), datetime_delay(seconds=self.__order_data['update_freq'])

    #
    #
    #
    def start(self, parent, data) -> None:
        super().start(parent, data)

    def stop(self, parent, data) -> None:
        super().stop(parent, data)

    def f(self, parent, data) -> (bool, tuple, Optional[str], Optional[datetime.datetime]):
        """
        f   is called at __utc_time

        return:
            done      = True  -> job Done        -> remove the job
                        False -> job not Done    -> call it again

            new_tasks = tuple with new tasks to add

            msg       = status message or None

            when      = when f has to be called again
                      = None                           -> call f instantly after

        """
        following, when = self._follow_symbol(data)
        if not following:
            return False, [], None, when

        #
        #
        #
        data_x, data_y = data['quote_server'].get_quote(symbol=self.symbol, all_data=False)
        if len(data_y) == 0:
            return False, [], None, datetime_delay(seconds=self.__order_data['update_freq'])
        data_x = data_x[0]
        data_y = data_y[0]

        #
        # update maximum price
        #
        if 'maximum_price' not in self.__order_data:
            self.__order_data['maximum_price'] = data_y
            return False, [], None, datetime_delay(seconds=self.__order_data['update_freq'])

        self.__order_data['maximum_price'] = max(self.__order_data['maximum_price'], data_y)

        #
        # rule
        #
        ratio = (data_y - self.__order_data['maximum_price']) / self.__order_data['maximum_price']

        if ratio <= self.__order_data['margin']:

            limit_price = data_y * (1.0 + (self.__order_data['margin'] / 10))  # TODO 0.1% -> 0.1%

            # send sell order
            return self.__sell_order(data, limit_price, kill_if_succeed=True)
        #
        #
        #
        return False, [], None, datetime_delay(seconds=self.__order_data['update_freq'])
