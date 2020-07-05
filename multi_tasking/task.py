from typing import Optional, Any

from multi_tasking.job_server import JobServer


#
#
#
class Task:
    identifier: int = -1
    started: bool = False

    #
    #
    #
    def __init__(self, identifier: int, state: dict = None):
        """Basic task initialization.

        Each derived object must execute the following code:
            super().__init__(identifier, state)
            if state is not None:
                # Task loaded from file
                #      recover the state
            else:
                # Task created
                #      initialize state

        Args:
            identifier: Job instance unique identifier.
            state: Saved state of the job.

        """
        self.started = False
        if state is not None:
            self.identifier = state['identifier']
        else:
            self.identifier = identifier

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
    def run(self, parent: JobServer, data: Any) -> (bool, tuple, Optional[str]):
        """Executes the job.

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.

        Returns:
            done: Boolean indicating if the job is done. If True, the job is
                  terminated and removed.
            new_tasks: Tuple defining the new tasks to add to the job list.
            msg: Status message.
        """
        raise NotImplementedError

    #
    #
    #
    def stop(self, parent: JobServer, data: Any) -> None:
        """Stops the job.

        Called when the job is done.

        Args:
            parent: JobServer object.
            data: Auxiliary data passed to the job by the JobServer.
        """
        raise NotImplementedError

    #
    #
    #
    def __str__(self) -> str:
        """Describes the job.

        Use:  return super().__str__() + ...

        Returns:
            Job description.
        """
        return str(self.identifier).ljust(2)

    #
    #
    #
    def state(self) -> Optional[dict]:
        """Returns the state of the job.

        Use:  return super().state() + {'...': ...., ...}

        Returns:
            dict: Information necessary to recover the state of the job
                  once out of the sleep state.
                  None means do not store the state of this job.
        """
        return {'identifier': self.identifier}
