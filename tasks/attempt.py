import datetime
from typing import Optional

from multi_tasking import TimerTask


#
#
#
class Attempt(TimerTask):
    operation_started = None

    def __init__(self, identifier, state=None):
        super().__init__(identifier, state)
        if state is not None:
            self.operation_started = state['operation_started']
        else:
            self.operation_started = False

    @staticmethod
    def __combine_text(text1, text2):
        if text1 is None:
            return text2
        if text2 is None:
            return text1
        return text1 + ' ' + text2

    def f(self, parent, data) -> (bool, tuple, Optional[str]):
        msg_check = None

        if self.operation_started:
            #
            # state 1
            #

            # Did the operation happen?
            ret, new_tasks, when, msg_check = self.did_operation_happen(parent, data)
            if ret:
                # yes -> kill job
                return True, new_tasks, msg_check, None
            if when is not None:
                # no -> but recheck
                return False, [], msg_check, when
            # no -> go to state 2
            self.operation_started = False

        #
        # state 2
        #

        # is operation possible?
        ret, when, motivation = self.is_operation_possible_now(parent, data)
        if not ret:
            return False, [], self.__combine_text(msg_check, motivation), when

        # start operation
        ret, when, msg_start = self.start_operation(parent, data)
        if not ret:
            # operation not started
            return False, [], self.__combine_text(msg_check, msg_start), when

        # operation started -> go to state 2
        self.operation_started = True
        return False, [], self.__combine_text(msg_check, msg_start), when

    def __str__(self) -> str:
        if self.operation_started:
            return super().__str__() + ' Check Attempt'
        else:
            return super().__str__() + ' Attempt'

    def state(self) -> Optional[dict]:
        c_state = super().state()
        c_state['operation_started'] = self.operation_started
        return c_state

    #
    #
    #
    def start(self, parent, data) -> None:
        """
            called just before the first run  ->  job started
                                              ->  re-started from sleep
        """
        pass

    def stop(self, parent, data) -> None:
        """
            called when the process is     Done
                                           Removed
        """
        pass

    def did_operation_happen(self, parent, data) -> (bool, tuple, Optional[datetime.datetime], Optional[str]):
        """
        return:
            done      = True  -> operation happened         -> kill job
                        False -> operation did not happened -> continue job

            new_tasks = tuple with new tasks to add              (only when done = True)

            when      = when to try again                        (only when done = False)
                        None -> don't try again -> restart operation

            msg       = check message
        """
        raise NotImplementedError

    def is_operation_possible_now(self, parent, data) -> (bool, Optional[datetime.datetime], Optional[str]):
        """
        return:
            possible    = True, False

            when        = when to try if it is not possible        (only when possible = False)

            motivation  = motivation why it is not possible        (only when possible = False)
        """
        raise NotImplementedError

    def start_operation(self, parent, data) -> (bool, Optional[datetime.datetime], Optional[str]):
        """
        return:
            started       = True, False

            when          = when to check      if started == true
                            when to re-try     if started == false

            msg           = msg of what has happened
        """
        raise NotImplementedError
