import datetime
from typing import Optional

from Tasks.Attempt import Attempt
from TradeInterface import datetime_delay, next_session, market_session


#
#
#
class OrderWhenOpen(Attempt):
    order_data = None

    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)
        if state is not None:
            self.order_data = state['order_data']
        else:
            self.order_data = dict()

    def __str__(self) -> str:
        pre_str = super().__str__() + '  ' + self.order_data['action'].ljust(9) + ' ' + self.order_data['symbol'].ljust(5)
        if self.order_data['action'] == 'BUY':
            return pre_str + ' @ ' + str(self.order_data['limit_price']).ljust(6) + '    qty = ' + str(self.order_data['quantity'])
        if self.order_data['action'] == 'SELL':
            return pre_str + ' @ ' + str(self.order_data['limit_price']).ljust(6) + '    qty = ' + str(self.order_data['quantity'])
        if self.order_data['action'] == 'SELL_STOP':
            return pre_str + ' @ ' + str(self.order_data['stop_price']).ljust(6) + '    qty = ' + str(self.order_data['quantity'])

    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['order_data'] = self.order_data
        return c_state

    #
    #
    #
    def start(self, parent, data) -> None:
        super().start(parent, data)

    def stop(self, parent, data) -> None:
        super().stop(parent, data)

    def did_operation_happen(self, parent, data) -> (bool, tuple, Optional[datetime.datetime], Optional[str]):
        if 'order_no' not in self.order_data:
            return True, [], None, 'error: order_no not state'

        if 'check' in self.order_data and self.order_data['check']:
            trade = data['trade']
            try:
                order_status, ex_price, ex_time = trade.check_order_status(self.order_data['order_no'])

                # order does not exists
                if order_status is None:
                    return True, [], None, 'error: order_no does not exists'

                # still open
                if order_status == 'OPEN' or order_status == 'CANCEL_REQUESTED':
                    # wait
                    return False, [], datetime_delay(minutes=10), 'order still open'

                # success
                if order_status == 'EXECUTED':
                    return True, [], None, 'order executed @ ' + ex_price + ' time = ' + ex_time

                # REJECTED, EXPIRED, CANCELLED
                return True, [], None, 'order ' + order_status.lower()
            except ValueError as e:
                return False, [], datetime_delay(minutes=10), str(e)
        return True, [], None, None

    def is_operation_possible_now(self, parent, data) -> (bool, Optional[datetime.datetime], Optional[str]):
        if market_session() == 'NO_TRADE':
            return False, next_session(), None
        return True, None, None

    def start_operation(self, parent, data) -> (bool, Optional[datetime.datetime], Optional[str]):
        trade = data['trade']

        self.order_data['order_no'] = None
        msg = ''
        try:

            if self.order_data['action'] == 'BUY':
                self.order_data['order_no'], msg = trade.place_limit_order(action='BUY', symbol=self.order_data['symbol'], quantity=self.order_data['quantity'], limit_price=self.order_data['limit_price'], order_term=self.order_data['order_term'], prev_order_id=self.order_data['prev_order_id'], session=market_session())

            if self.order_data['action'] == 'SELL':
                self.order_data['order_no'], msg = trade.place_limit_order(action='SELL', symbol=self.order_data['symbol'], quantity=self.order_data['quantity'], limit_price=self.order_data['limit_price'], order_term=self.order_data['order_term'], prev_order_id=self.order_data['prev_order_id'], session=market_session())

            if self.order_data['action'] == 'SELL_STOP':
                self.order_data['order_no'], msg = trade.place_stop_order(action='SELL', symbol=self.order_data['symbol'], quantity=self.order_data['quantity'], stop_price=self.order_data['stop_price'], order_term=self.order_data['order_term'], prev_order_id=self.order_data['prev_order_id'], session=market_session())

            if self.order_data['order_no'] is None:
                return True, datetime_delay(minutes=1), 'trade returned None'

        except ValueError as e:
            return False, datetime_delay(minutes=1), str(e)

        return True, datetime_delay(seconds=3), msg + ' order_no = ' + str(self.order_data['order_no'])

    #
    #
    #


