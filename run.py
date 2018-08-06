import sys
import json
import platform
import threading
from TradeInterface import TradeInterface
from Multitasking import JobServer
from TradingPlatformServers import QuoteServer, GraphServer
from Tasks import KeepAliveTask
from TradingPlatformShell import ShellServer


#
# parse command line
#
clear_jobs = False
use_sandbox = False
for arg in sys.argv[1:]:
    if arg.lower() == 'clear':
        clear_jobs = True
        print('clear existing jobs')
    if arg.lower() == 'sandbox':
        use_sandbox = True
        print('use sandbox')


#
# Load keys <- keys.txt
#
with open('keys.txt', 'r') as fp:
    keys = json.load(fp)


#
# Load Preferences
#
with open('preferences.txt', 'r') as fp:
    preferences = json.load(fp)


#
# Load Settings
#
with open('settings.txt', 'r') as fp:
    settings = json.load(fp)
browser_path = settings['browser_path_' + platform.system()]
quote_update_time = settings['quote_update_time_sec']
job___update_time = settings['job___update_time_sec']


#
#
#
#
#
#
print('*')
print('*   Trading Interface')
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
print('YOUR E*TRADE ACCOUNT AND IT CAN AUTOMATICALLY PLACE ORDERS THAT YOU DO OR YOU')
print('DO NOT WANT.')

print('*')
print('THIS IS NOT A BUG FREE SOFTWARE AND MANY FUNCTIONALITIES HAVE NOT BEEN TESTED.')

print('THIS SOFTWARE IS PROVIDED OPEN SOURCE FOR EDUCATIONAL PURPOSES ONLY.')

print('USE THIS SOFTWARE AT YOUR OWN RISK.')
print('*')
while True:
    answer = input('Do you agree [y/n]? ').lower()
    if answer == 'y':
        break
    if answer == 'n' or answer == 'no':
        exit(0)
print('')

#
# Start JobServer
#
job_server = JobServer()
job_server.load_or_create(status_file_path='status.pickle', clear_jobs=clear_jobs)
job_server.time_frequency_sec = job___update_time


#
# Init TradeInterface
#
trader_interface = TradeInterface(keys=keys, dev=use_sandbox, browser_path=browser_path)


#
# Init QuoteServer
#
quote_server = QuoteServer(trader_interface)
QuoteServer.time_frequency_sec = quote_update_time

#
# Init GraphServer
#
graph_server = GraphServer()

#
# Share   -> JobServer
#         -> TradeInterface
#         -> GraphServer
#         -> QuoteServer
#
aux_data = {'job_server': job_server,
            'trade': trader_interface,
            'quote_server': quote_server,
            'figure_server': graph_server,
            'preferences': preferences,
            'main_thread_quit_event': threading.Event(),
            'settings': settings
            }

job_server.aux_data = aux_data
graph_server.aux_data = aux_data
shell_server = ShellServer(aux_data)


#
#
#
# Connect TradeInterface
#
print('Connecting to the trading platform...')
if not trader_interface.connect():
    exit(0)

try:
    trader_interface.select_account()

    #
    # Create KeepAliveTask (after the trader has started)
    #
    job_server.add(KeepAliveTask(job_server.next_valid_task_id()))

    #
    # start   JobServer
    #         QuoteServer
    #         ShellServer
    #
    job_server.start()
    quote_server.start()
    shell_server.start()

    #
    # Main Loop
    #
    graph_server.loop()
    #
    #
    #
except Exception as e:
    print(str(e))
    #
    #
finally:
    #
    # stop Shell Server
    #
    if shell_server.is_alive():
        shell_server.join()

    #
    # JobServer is not running here unless exception has happened
    #
    if job_server.is_alive():
        job_server.quit()
        job_server.join()
        job_server.list_done_tasks()

    #
    # stop QuoteServer
    #
    if quote_server.is_alive():
        quote_server.quit()
        quote_server.join()

    #
    # stop TradeInterface
    #
    try:
        trader_interface.disconnect()
        print('Trading platform disconnected.')
    except Exception as e:
        print('Trading platform disconnection: FAILED')
        print(str(e))
    #
    #
    print('Main thread stopped.')
