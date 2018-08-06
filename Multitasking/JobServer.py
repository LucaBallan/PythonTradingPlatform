import threading
import os.path
import pickle
import copy
import importlib


#
#
#
class JobServer(threading.Thread):
    #
    aux_data = None
    time_frequency_sec = 1.0

    #
    # core (_mutex)
    #
    _mutex = None
    _task_list = None
    __remove_list = None
    __exiting = None

    #
    # Id    (__next_id_mutex)
    #
    __next_id_mutex = None
    __next_valid_id = None

    #
    # messages (_mutex)
    #
    _done_list_feedback = None
    _removed_list_feedback = None
    _msg_feedback = None
    __status_file_path = None

    #
    #
    #
    def __init__(self):
        super().__init__()
        self.setName('JobServer')
        self.__status_file_path = None
        #
        #
        #
        self._mutex = threading.Lock()
        self._task_list = []
        self.__remove_list = []
        self.__exiting = threading.Event()
        self._done_list_feedback = []
        self._removed_list_feedback = []
        self._msg_feedback = []
        #
        #
        #
        self.__next_id_mutex = threading.Lock()
        self.__next_valid_id = 0
        #
        #
        #

    #
    #
    #
    def next_valid_task_id(self) -> int:
        self.__next_id_mutex.acquire()
        n = self.__next_valid_id
        self.__next_valid_id += 1
        self.__next_id_mutex.release()
        return n

    #
    #
    #
    def run(self):
        while True:
            #
            # wait and check exiting
            #
            if self.__exiting.wait(self.time_frequency_sec):
                break

            #
            # Start
            #
            self._mutex.acquire()

            #
            # process remove requests
            #
            tmp_list = []
            for a in self._task_list:
                if a.identifier in self.__remove_list:
                    a.stop(self, self.aux_data)
                    self._removed_list_feedback.append(a.identifier)
                else:
                    tmp_list.append(a)
            self._task_list = tmp_list
            self.__remove_list = []

            #
            # Consistency check
            #
            identifiers = [a.identifier for a in self._task_list]
            if len(set(identifiers)) != len(identifiers):
                print('duplicate identifiers')
                exit(1)

            #
            # Process
            #
            to_add_list = []
            done_list = []
            for a in self._task_list:
                if not a.started:
                    a.start(self, self.aux_data)                                 # Start
                    a.started = True
                done, new_tasks, msg = a.run(self, self.aux_data)                # Run
                if done:
                    done_list.append(a.identifier)
                for new_task in new_tasks:
                    to_add_list.append(new_task)
                if msg is not None:
                    self._msg_feedback.append(msg)

            #
            # Remove done Tasks
            #
            if len(done_list) != 0:
                tmp_list = []
                for a in self._task_list:
                    if a.identifier in done_list:
                        a.stop(self, self.aux_data)                              # Stop
                    else:
                        tmp_list.append(a)
                self._task_list = tmp_list
                self._done_list_feedback += done_list

            #
            # Add new Tasks
            #
            self._task_list += to_add_list

            #
            # End
            #
            self._mutex.release()

        #
        #
        #
        self.__save_status()
        print('JobServer stopped.')

    #
    #
    #
    def list_done_tasks(self, display_done_and_removed=True):
        msg1 = ''
        msg2 = ''
        msg3 = False
        #
        #
        self._mutex.acquire()
        #
        #
        if len(self._msg_feedback) != 0:
            for msg in self._msg_feedback:
                print(msg)
            self._msg_feedback = []
            msg3 = True
        if len(self._done_list_feedback) != 0:
            msg1 = '[' + (', '.join([str(idx) for idx in self._done_list_feedback])) + '] done.'
            self._done_list_feedback = []
        if len(self._removed_list_feedback) != 0:
            msg2 = '[' + (', '.join([str(idx) for idx in self._removed_list_feedback])) + '] removed.'
            self._removed_list_feedback = []
        #
        #
        self._mutex.release()
        #
        #
        if display_done_and_removed:
            if len(msg1) != 0:
                print(msg1)
            if len(msg2) != 0:
                print(msg2)
        if (len(msg1) != 0) or (len(msg2) != 0) or msg3:
            print()

    #
    #
    #
    def list_open_tasks(self):
        self._mutex.acquire()
        for a in self._task_list:
            print(a)
        print()
        self._mutex.release()

    #
    #
    #
    def add(self, task):
        self._mutex.acquire()
        self._task_list.append(task)
        self._mutex.release()

    #
    #
    #
    def remove(self, task_id):
        self._mutex.acquire()
        if task_id in [a.identifier for a in self._task_list]:
            self.__remove_list.append(task_id)
        else:
            print(str(task_id) + ' not found')
            print()
        self._mutex.release()

    #
    #
    #
    def quit(self):
        self._mutex.acquire()
        self.__exiting.set()
        self._mutex.release()

    #
    #
    #
    def __save_status(self):
        if self.__status_file_path:
            self._mutex.acquire()
            self.__next_id_mutex.acquire()
            #
            status = [self.__next_valid_id, self.__remove_list]
            for a in self._task_list:
                a_state = a.state()
                if a_state is not None:
                    status.append([a.__class__.__name__, a_state])
            pickle.dump(status, open(self.__status_file_path, 'wb'))
            #
            self.__next_id_mutex.release()
            self._mutex.release()

    #
    #
    #
    def load_or_create(self, status_file_path, clear_jobs):
        self.__status_file_path = status_file_path
        if (not clear_jobs) and os.path.isfile(status_file_path):
            o = pickle.load(open(status_file_path, 'rb'))
            self.__next_valid_id = o[0]
            self.__remove_list = copy.deepcopy(o[1])
            for task_desc in o[2:]:
                class_module = importlib.import_module("Tasks")
                class_type = getattr(class_module, task_desc[0])
                task = class_type(None, task_desc[1])
                self.add(task)
            if (len(self._task_list) == 0) and (len(self.__remove_list) == 0):
                self.__next_valid_id = 0
