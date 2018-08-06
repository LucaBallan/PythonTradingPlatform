import datetime
from typing import Optional
from Tasks.AbstractTask import AbstractTask
from TradeInterface import current_time


#
#
#
class TimerTask(AbstractTask):
    __utc_time = None

    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)
        if state is not None:
            self.__utc_time = state['__utc_time']
        else:
            self.__utc_time = current_time()

    def run(self, parent, data) -> (bool, tuple, Optional[str]):
        # check time
        eastern_time_now = current_time()
        if eastern_time_now >= self.__utc_time:
            # operate
            done, new_tasks, msg, when = self.f(parent, data)
            # set next time
            if when is not None:
                self.__utc_time = when
            # done
            if done:
                return True, new_tasks, (str(self.identifier) + ': ' + msg) if msg is not None else None
            # not done
            return False, new_tasks, (str(self.identifier) + ': ' + msg) if msg is not None else None

        # not ready
        return False, [], None

    def __str__(self) -> str:
        return super().__str__() + ' TimerTask @ ' + self.__utc_time.strftime('%Y-%m-%d %H:%M')

    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['__utc_time'] = self.__utc_time
        return c_state

    #
    #
    #
    def start(self, parent, data) -> None:
        """
            called just before the first run  ->  job started
                                              ->  re-started from sleep
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def stop(self, parent, data) -> None:
        """
            called when the process is     Done
                                           Removed
        """
        raise NotImplementedError
