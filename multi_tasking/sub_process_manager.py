import signal
from subprocess import Popen, PIPE
from typing import Optional


#
#
#
class SubProcessManager:
    """
        - based on "subprocess"
        - memory efficient
        - limited communication
    ​"""

    _processes = None

    def __init__(self) -> None:
        self._processes = dict()

    #
    #
    #
    def add(self, index: str, commandline: str, debug_stdout: bool) -> None:
        if index in self._processes:
            if self._processes[index]['process'].poll() is None:
                return
            else:
                self.remove(index)

        self._processes[index] = dict()
        self._processes[index]['process'] = Popen(commandline, stdin=PIPE, stdout=None if debug_stdout else PIPE, bufsize=1, shell=False)               # TODO bufsize

    #
    #
    #
    def remove(self, index: str) -> None:
        if index not in self._processes:
            return

        # terminate
        if self._processes[index]['process'].poll() is None:
            self._processes[index]['process'].send_signal(signal.SIGTERM)
            self._processes[index]['process'].wait()
        # delete objects
        for obj in list(self._processes[index].keys()):
            del obj
        # delete entry
        del self._processes[index]

    #
    #
    #
    def remove_all(self) -> None:
        for index in list(self._processes.keys()):
            self.remove(index)

    #
    #
    #
    def send(self, index: str, message: str) -> None:
        if index not in self._processes:
            return
        if self._processes[index]['process'].poll() is None:
            self._processes[index]['process'].stdin.write(str.encode(message + '\n'))
            self._processes[index]['process'].stdin.flush()

    #
    #
    #
    def receive_blocking(self, index: str) -> Optional[str]:
        if index not in self._processes:
            return None
        if self._processes[index]['process'].poll() is None:
            return self._processes[index]['process'].stdout.readline().decode()
