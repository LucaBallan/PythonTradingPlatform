import datetime
from typing import Optional
from Tasks.TimerTask import TimerTask
from TradeInterface import datetime_delay


#
#
#
class KeepAliveTask(TimerTask):
    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)

    def f(self, parent, data) -> (bool, tuple, Optional[str], Optional[datetime.datetime]):
        trade = data['trade']
        try:
            trade.get_account_balance()
        except ValueError as e:
            return False, [], str(e), datetime_delay(minutes=45)

        return False, [], None, datetime_delay(minutes=45)

    def __str__(self) -> str:
        return super().__str__() + ' KeepConnectionAlive'

    def state(self) -> Optional[dict]:
        return None

    def start(self, parent, data) -> None:
        return

    def stop(self, parent, data) -> None:
        return
