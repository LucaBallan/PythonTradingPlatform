import threading
import InteractiveShell
from TradingPlatformShell.Actions1 import *
from TradingPlatformShell.Actions2 import *


#
#
#
class ShellServer(threading.Thread):
    aux_data = None

    #
    #
    #
    def __init__(self, aux_data):
        super().__init__()
        self.aux_data = aux_data

    #
    #
    #
    def run(self):
        #
        #
        #
        list_aliases = {'x': 'exit',
                        'j': 'jobs',
                        'r': 'remove',
                        #
                        'o': 'orders',
                        'p': 'positions',
                        'q': 'quote',
                        't': 'time',
                        'bal': 'balance',
                        #
                        'c': 'cancel',
                        #
                        'b': 'buy',
                        's': 'sell',
                        'pr': 'protect',
                        #
                        '*b': '*buy',
                        '*s': '*sell',
                        '*pr': '*protect',
                        #
                        '**b': '**buy',
                        '**s': '**sell',
                        '**pr': '**protect',
                        }

        action_table = [['', [0, action_default]],
                        ['exit', [0, action_quit, '', 'exit platform']],
                        ['jobs', [0, action_jobs_list, '', 'list all the jobs']],
                        ['remove', [1, action_jobs_remove, 'job_id', 'remove a job from the job list']],
                        [],
                        ['orders', [0, action_order_list, '', 'list active orders']],
                        ['positions', [0, action_positions_list, '', 'list positions']],
                        ['time', [0, action_time, '', 'utc time']],
                        ['balance', [0, action_balance, '', 'get account balance']],
                        [],
                        ['quote', [1, action_quote, 'symbol', 'get a quote for the equity']],
                        [],
                        ['server', [0, action_list_quote, '', 'list the quotes that are currently followed']],
                        ['w', [1, action_w_create, 'symbol', 'create a real time window']],
                        ['*', [1, action_w_remove, 'symbol/*', 'delete a real time window (* delete all)']],
                        [],
                        ['=', [1, action_calc, 'src [trg] [qty]', '% difference or evaluate expression', help_calc]],
                        [],
                        ['check', [1, action_check, 'order_num', 'check an order']],
                        ['cancel', [1, action_cancel, 'order_num', 'cancel an order']],
                        [],
                        ['buy', [3, action_buy,                 'symbol value price [session=R] [order_no]', 'buy   below price', help_buy]],
                        ['sell', [2, action_sell,               'symbol price       [session=R] [order_no]', 'sell  above limit', help_sell]],
                        ['protect', [2, action_sell_stop,       'symbol margin      [session=R] [order_no]', 'sell  if below stop', help_sell_stop]],
                        ['trail', [2, action_sell_trailing,     'symbol margin                  [order_no]', 'sell  if below stop % (realtime)', help_trail]],
                        ]

        #
        #
        # console
        #
        console = InteractiveShell.Console(words_list=self.aux_data['settings']['autocomplete'], history_filename=None, ctrl_c_command='exit', auto_suggest=False)
        self.aux_data['console'] = console

        #
        # loop
        #
        try:
            InteractiveShell.command_prompt(console, action_table, list_aliases=list_aliases, aux_data=self.aux_data)
        except Exception as e:
            print('shell: ' + str(e))

        #
        # Quit Main Thread
        #
        self.aux_data['main_thread_quit_event'].set()
