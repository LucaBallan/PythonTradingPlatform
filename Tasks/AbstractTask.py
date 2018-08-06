from typing import Optional


#
#
#
class AbstractTask:
    identifier = None
    started = None

    def __init__(self, identifier, state=None):
        self.started = False
        if state is not None:
            self.identifier = state['identifier']
        else:
            self.identifier = identifier
        """
        USE: 
            super().__init__(identifier, state)
            if state is not None:
                # Task loaded from file
                #      recover the state
            else:
                # Task created
                #      initialize state
        """

    def start(self, parent, data) -> None:
        """
            called just before the first run  ->  job started
                                              ->  re-started from sleep
        """
        raise NotImplementedError

    def run(self, parent, data) -> (bool, tuple, Optional[str]):
        """
        run   is called as frequently as possible

        return:
            done      = True  -> job Done        -> remove the job
                        False -> job not Done    -> call it again

            new_tasks = tuple with new tasks to add

            msg       = status message or None
        """
        raise NotImplementedError

    def stop(self, parent, data) -> None:
        """
            called when the process is     Done
                                           Removed
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """
            str       = string to visualize

            Use:  return super().__str__() + ...
        """
        return str(self.identifier).ljust(2)

    def state(self) -> Optional[dict]:
        """
            dict      = all the important variables to recover the state
            None      = do not save this Task

            Use:  return super().state() + {'...': ...., ...}
        """
        return {'identifier': self.identifier}
    #
    #
    #
