import datetime
from typing import Optional

import numpy

from MultiTasking.TimerTask import TimerTask
from TradeInterface import next_session, market_session


#
#
#
class FollowSymbolTask(TimerTask):
    symbol = None
    __following_symbol = None

    #
    #
    #
    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)
        self.__following_symbol = False
        if state is not None:
            self.symbol = state['symbol']
        else:
            self.symbol = None

    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['symbol'] = self.symbol
        return c_state

    #
    #
    #
    def _follow_symbol(self, data) -> (bool, Optional[datetime.datetime]):
        """
            True  -> is following
            False -> when to retry
        """
        #
        # closed market
        #
        if market_session() == 'NO_TRADE':
            if self.__following_symbol:
                data['quote_server'].remove_quote(self.symbol)
                self.__following_symbol = False
            return False, next_session()

        #
        # open market
        #
        if not self.__following_symbol:
            data['quote_server'].add_quote(self.symbol)
            self.__following_symbol = True
        return True, None

    #
    #
    #
    def _unfollow_symbol(self, data):
        if self.__following_symbol:
            data['quote_server'].remove_quote(self.symbol)
            self.__following_symbol = False

    #
    #
    #
    def inherit_follow_from(self, task):
        """
            Get the handle of the QuoteServer before it is lost
        """
        # TODO
        if not isinstance(task, FollowSymbolTask):
            raise ValueError('task must be a FollowSymbolTask')
        self.symbol = task.symbol
        if task.__following_symbol:
            self.__following_symbol = True
            task.__following_symbol = False

    #
    #
    #
    def _pre_process_data(self, data):
        #
        # TODO check that quote_server does not have gap between time
        # TODO otherwise it will look like a big jump
        #

        # TODO FILTER -> restrict to a window -> or subsample -> this is most of the time
        # b, a = butter(3, 0.05)
        # y = filtfilt(b, a, xn)
        # from pykalman -> Kalman and Unscented
        # Kalma

        data_x, data_y = data['quote_server'].get_quote(symbol=self.symbol, all_data=True)
        derivative = numpy.abs(data_x[1:] - data_x[:-1])
        occurrences = numpy.where(derivative >= 3 * data['quote_server'].time_frequency_sec)
        if len(occurrences) != 0:
            data_x = data_x[occurrences[-1]:]
            data_y = data_y[occurrences[-1]:]
        return data_x, data_y

    #
    #
    #
    def start(self, parent, data) -> None:
        """
            called just before the first run  ->  job started
                                              ->  re-started from sleep
        """
        pass

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

        USAGE:
            following, when = self._follow_symbol(data)
            if not following:
                return False, [], None, when
        """

        raise NotImplementedError

    def stop(self, parent, data) -> None:
        """
        USAGE:
            super().stop(parent, data)
        """
        self._unfollow_symbol(data)
