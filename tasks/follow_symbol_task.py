import datetime
from typing import Optional, Any

import numpy

from multi_tasking import Task, TimerTask, JobServer
from trade_interface import next_session, market_session


#
#
#
class FollowSymbolTask(TimerTask):
    _symbol = None
    __following_symbol = None

    #
    #
    #
    def __init__(self, identifier: int, state: dict = None):
        super().__init__(identifier, state)
        self.__following_symbol = False
        if state is not None:
            self._symbol = state['symbol']
        else:
            self._symbol = None

    #
    #
    #
    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['symbol'] = self._symbol
        return c_state

    #
    #
    #
    def _follow_symbol(self, data: Any) -> (bool, Optional[datetime.datetime]):
        """
            True  -> is following
            False -> when to retry
        """
        #
        # closed market
        #
        if market_session() == 'NO_TRADE':
            if self.__following_symbol:
                data['quote_server'].remove_quote(self._symbol)
                self.__following_symbol = False
            return False, next_session()

        #
        # open market
        #
        if not self.__following_symbol:
            data['quote_server'].add_quote(self._symbol)
            self.__following_symbol = True
        return True, None

    #
    #
    #
    def _unfollow_symbol(self, data: Any) -> None:
        if self.__following_symbol:
            data['quote_server'].remove_quote(self._symbol)
            self.__following_symbol = False

    #
    #
    #
    def inherit_follow_from(self, task: Task) -> None:
        """
            Get the handle of the QuoteServer before it is lost
        """
        # TODO
        if not isinstance(task, FollowSymbolTask):
            raise ValueError('The current task must be a FollowSymbolTask instance.')
        self._symbol = task._symbol
        if task.__following_symbol:
            self.__following_symbol = True
            task.__following_symbol = False

    #
    #
    #
    def _pre_process_data(self, data: Any):
        #
        # TODO check that quote_server does not have gap between time
        # TODO otherwise it will look like a big jump
        #

        # TODO FILTER -> restrict to a window -> or subsample -> this is most of the time
        # b, a = butter(3, 0.05)
        # y = filtfilt(b, a, xn)
        # from pykalman -> Kalman and Unscented
        # Kalma

        data_x, data_y = data['quote_server'].get_quote(symbol=self._symbol, all_data=True)
        derivative = numpy.abs(data_x[1:] - data_x[:-1])
        occurrences = numpy.where(derivative >= 3 * data['quote_server'].time_frequency_sec)
        if len(occurrences) != 0:
            data_x = data_x[occurrences[-1]:]
            data_y = data_y[occurrences[-1]:]
        return data_x, data_y

    #
    #
    #
    def start(self, parent: JobServer, data: Any) -> None:
        """Initializes the job.

        This function is called just before its first run, or when it restarted
        from sleep.

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.
        """
        pass

    def f(self, parent: JobServer, data: Any) -> (bool, tuple, Optional[str], Optional[datetime.datetime]):
        """Executes the job task at specific time.

        USAGE:
            following, when = self._follow_symbol(data)
            if not following:
                return False, [], None, when

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.

        Returns:
            done: Boolean indicating if the job is done. If True, the job is
                  terminated and removed.
            new_tasks: Tuple defining the new tasks to add to the job list.
            msg: Status message.
            when: Time when f has to be called again. If None, call f right
                  after.
        """
        raise NotImplementedError

    def stop(self, parent: JobServer, data: Any) -> None:
        """Stops the job.

        Called when the job is done.
        USAGE:
            super().stop(parent, data)

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.
        """
        self._unfollow_symbol(data)
