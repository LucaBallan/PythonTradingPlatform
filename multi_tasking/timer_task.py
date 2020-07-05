import datetime
from typing import Optional, Any

from multi_tasking.job_server import JobServer
from multi_tasking.task import Task
from trade_interface import current_time


#
#
#
class TimerTask(Task):

    #
    #
    #
    def __init__(self, identifier: int, state: dict = None):
        super().__init__(identifier, state)
        if state is not None:
            self.__utc_time = state['__utc_time']
        else:
            self.__utc_time = current_time()

    #
    #
    #
    def run(self, parent: JobServer, data: Any) -> (bool, tuple, Optional[str]):
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

    #
    #
    #
    def __str__(self) -> str:
        return super().__str__() + ' TimerTask @ ' + self.__utc_time.strftime('%Y-%m-%d %H:%M')

    #
    #
    #
    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['__utc_time'] = self.__utc_time
        return c_state

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
        raise NotImplementedError

    #
    #
    #
    def f(self, parent: JobServer, data: Any) -> (bool, tuple, Optional[str],
                                                               Optional[datetime.datetime]):
        """Executes the job task at specific time.

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

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.
        """
        raise NotImplementedError
