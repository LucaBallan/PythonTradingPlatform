import threading
import warnings
import matplotlib
from sys import platform as sys_pf
if sys_pf == 'darwin':
    print('[use TkAgg]')
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from functools import partial


#
#
#
#
#
#
class GraphServer:
    aux_data = None
    __mutex = None
    __mutex_inner = None
    __figure_list = None
    __to_add = None

    #
    #
    #
    def __init__(self):
        self.__figure_list = []
        self.__to_add = []
        self.__mutex = threading.Lock()
        self.__mutex_inner = threading.Lock()
        warnings.filterwarnings("ignore", ".*GUI is implemented.*")

    #
    #
    #
    def add_figure(self, symbol):
        symbol = symbol.upper().strip()
        #
        self.__mutex.acquire()
        if symbol in self.__to_add:
            self.__mutex.release()
            return
        if symbol in [f[0] for f in self.__figure_list]:
            self.__mutex.release()
            return
        self.__mutex.release()
        #
        self.aux_data['quote_server'].add_quote(symbol)
        #
        self.__mutex.acquire()
        self.__to_add.append(symbol)
        self.__mutex.release()

    #
    #
    #
    def remove_figure(self, symbol):
        symbol = symbol.upper().strip()
        self.__mutex_inner.acquire()
        for f in self.__figure_list:
            if f[0] == symbol:
                f[0] = None
        self.__mutex_inner.release()
        self.aux_data['quote_server'].remove_quote(symbol)

    #
    #
    #
    def list_figure(self):
        return [f[0] for f in self.__figure_list]

    #
    #
    #
    @staticmethod
    def handle_close(_, fig, self):
        for f in self.__figure_list:
            if f[1] == fig:
                if f[0] is not None:
                    f[0] = None
                    print('closed')

    # def press(event):
    #     print('press', event.key)
    #     sys.stdout.flush()
    #     if event.key == 'x':
    #         visible = xl.get_visible()
    #         xl.set_visible(not visible)
    #         fig.canvas.draw()

    #
    #
    #
    def loop(self):
        listener_event = self.aux_data['quote_server'].add_listener()
        plt.ion()

        #
        # loop
        #
        while True:
            #
            # create (add)
            #
            self.__mutex.acquire()
            if len(self.__to_add) != 0:
                for symbol in self.__to_add:
                    #
                    fig = plt.figure()
                    fig.canvas.set_window_title(symbol)
                    fig.canvas.mpl_connect('close_event', partial(self.handle_close, fig=fig, self=self))
                    ax = fig.add_subplot(111, autoscale_on=True)
                    ax.set_title(symbol)
                    ax.autoscale(enable=True, axis='x', tight=True)
                    ax.grid(True, color='0.9', zorder=0)
                    fig.tight_layout()
                    line, = ax.plot([], 'o-', color='C0')
                    #
                    fig.show()
                    self.__figure_list.append([symbol, fig, ax, line])
                self.__to_add = []
            self.__mutex.release()

            #
            # delete
            #
            self.__mutex_inner.acquire()
            [plt.close(f[1]) for f in self.__figure_list if f[0] is None]
            self.__figure_list = [f for f in self.__figure_list if f[0] is not None]
            self.__mutex_inner.release()

            #
            # update
            #
            if listener_event.wait(0.1):
                listener_event.clear()

                self.__mutex_inner.acquire()
                try:
                    for f in self.__figure_list:
                        if f[0] is not None:
                            data_x, data_y = self.aux_data['quote_server'].get_quote(f[0], all_data=True)
                            if len(data_x) != 0:
                                title = f[0] + '  ' + data_x[-1].strftime("%H:%M:%S").ljust(8) + '    {0:.2f}'.format(data_y[-1])
                                f[2].set_title(title)
                                f[2].get_yaxis().get_major_formatter().set_scientific(False)
                                f[2].xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
                                f[2].xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
                                f[3].set_data(data_x, data_y)
                                f[2].relim()                              # recompute the data limits TODO blocked by HOME Button!!!
                                f[2].autoscale_view(scalex=True, scaley=True, tight=True)           # automatic axis scaling
                                f[1].canvas.flush_events()                # update the plot and take care of window events (like resizing etc.)
                except Exception as e:
                    print('closing event -> ' + str(e))
                self.__mutex_inner.release()

            #
            # handle window events
            #
            for f in self.__figure_list:
                f[1].canvas.start_event_loop(0.2 / len(self.__figure_list))

            #
            # check quit
            #
            if self.aux_data['main_thread_quit_event'].is_set():
                for f in self.__figure_list:
                    plt.close(f[1])
                break

        #
        #
        #
        print('GraphServer stopped.')
