import json
import os
import platform
import sys
import threading

from MultiTasking import JobServer, SubProcessManager
from Tasks import KeepConnectionAlive
from TradeInterface import TradeInterface
from TradingPlatformServers import QuoteServer, GraphServer
from TradingPlatformShell import ShellServer

#
#
#
if __name__ == '__main__':
    # Default configuration.
    offline = False

    # Ensure to run in root directory.
    current_src_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(current_src_path)

    print('*')
    print('*   Trading Platform')
    print('*   Copyright (c) 2018 Luca Ballan')
    print('*')
    print('THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR')
    print('IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,')
    print('FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE')
    print('AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER')
    print('LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,')
    print('OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE')
    print('SOFTWARE.')
    print('*')
    print('BY USING THIS SOFTWARE YOU ARE ACCEPTING THE FACT THAT IT WILL HAVE ACCESS TO ALL')
    print('YOUR E*TRADE ACCOUNT DATA, AND THAT IT CAN AUTOMATICALLY PLACE ORDERS THAT YOU DO')
    print('OR YOU DO NOT WANT.')
    print('*')
    print('THIS IS NOT A BUG FREE SOFTWARE AND MANY FUNCTIONALITIES HAVE NOT BEEN TESTED.')
    print('USE THIS SOFTWARE AT YOUR OWN RISK.')
    print('*')
    while True:
        answer = input('Do you agree [y/n]? ').lower()
        if answer == 'y':
            break
        if answer == 'n' or answer == 'no':
            exit(0)
    print('')

    # Parse command line.
    clear_jobs = False
    use_sandbox = False
    for arg in sys.argv[1:]:
        if arg.lower() == 'clear':
            clear_jobs = True
            print('Clear existing jobs.')
        if arg.lower() == 'sandbox':
            use_sandbox = True
            print('Use sandbox.')

    # Load keys.
    with open('keys.txt', 'r') as fp:
        keys = json.load(fp)
        if (use_sandbox and keys['sandbox']['consumer_key'] == '') or (not use_sandbox and keys['production']['consumer_key'] == ''):
            print('Consumer key and secret need to be set in keys.txt for the platform to connect to your account.')
            print('See README.md for additional information.')
            print('')
            exit(0)

    # Load preferences.
    with open('preferences.txt', 'r') as fp:
        preferences = json.load(fp)

    # Load settings.
    with open('settings.txt', 'r') as fp:
        settings = json.load(fp)
    browser_path = settings['browser_path_' + platform.system()]
    quote_update_time = settings['quote_update_time_sec']
    job___update_time = settings['job___update_time_sec']

    # Start JobServer.
    job_server = JobServer()
    job_server.load_or_create(status_file_path='status.pickle', clear_jobs=clear_jobs)
    job_server.time_frequency_sec = job___update_time

    # Init TradeInterface.
    trade_interface = TradeInterface(keys=keys, use_sandbox=use_sandbox, browser_path=browser_path)

    # Init QuoteServer.
    quote_server = QuoteServer(trade_interface)
    QuoteServer.time_frequency_sec = quote_update_time

    # Init GraphServer
    graph_server = GraphServer()
    quote_figure_manager = SubProcessManager()

    # Share data across tasks -> JobServer
    #                         -> TradeInterface
    #                         -> GraphServer
    #                         -> QuoteFigureServer
    #                         -> QuoteServer
    aux_data = {'job_server': job_server,
                'trade': trade_interface,
                'quote_server': quote_server,
                'figure_server': graph_server,
                'quote_figure_manager': quote_figure_manager,
                'preferences': preferences,
                'main_thread_quit_event': threading.Event(),
                'settings': settings,
                }
    job_server.aux_data = aux_data
    graph_server.aux_data = aux_data
    shell_server = ShellServer(aux_data)

    # Connect trade_interface.
    if not offline:
        print('Connecting to the trading platform...')
        if not trade_interface.connect():
            exit(0)

    try:
        # Init trade_interface.
        if not offline:
            trade_interface.select_account()
            job_server.add(KeepConnectionAlive(job_server.next_valid_task_id()))

        # Start job_server, quote_server, shell_server.
        job_server.start()
        quote_server.start()
        shell_server.start()

        # Main Loop.
        graph_server.loop()

    except Exception as e:
        print(str(e))

    finally:
        # Stop shell server.
        if shell_server.is_alive():
            shell_server.join()

        # Check if job_server is still alive and stop it.
        # It should not be running here unless an exception had happened.
        if job_server.is_alive():
            job_server.quit()
            job_server.join()
            job_server.list_done_tasks()

        # Stop quote_server.
        if quote_server.is_alive():
            quote_server.quit()
            quote_server.join()

        # Stop trade_interface.
        if not offline:
            try:
                trade_interface.disconnect()
                print('Trading platform disconnected.')
            except Exception as e:
                print('Trading platform disconnection: FAILED')
                print(str(e))

        # Kill all quote_figure in manager.
        quote_figure_manager.remove_all()

        print('Main thread stopped.')
