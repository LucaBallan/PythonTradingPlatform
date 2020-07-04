import datetime
from typing import Optional, Any

from MultiTasking.JobServer import JobServer
from MultiTasking.TimerTask import TimerTask
from TradeInterface import datetime_delay


#
#
#
class KeepConnectionAlive(TimerTask):
    def __init__(self, identifier: int, state: dict = None):
        super().__init__(identifier, state)

    def f(self, parent: JobServer, data: Any) -> (bool, tuple, Optional[str],
                                                  Optional[datetime.datetime]):
        try:
            data['trade'].get_account_balance()
        except ValueError as e:
            return False, [], str(e), datetime_delay(minutes=45)
        return False, [], None, datetime_delay(minutes=45)

    def __str__(self) -> str:
        return super().__str__() + ' KeepConnectionAlive'

    def state(self) -> Optional[dict]:
        return None

    def start(self, parent: JobServer, data: Any) -> None:
        return

    def stop(self, parent: JobServer, data: Any) -> None:
        return
