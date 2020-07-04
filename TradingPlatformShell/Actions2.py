import math

import Tasks
from TradeInterface import format_order_action
from TradingPlatformShell.StringParsers import *
from TradingPlatformShell.Utils import *


#
#
#
def read_preferences(obj_, preferences_):
    if obj_ in preferences_:
        return list(preferences_[obj_])
    else:
        return list(preferences_['default'])


#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
def help_buy():
    print('')
    print('    buy symbol value price R           ->          market order    (default)')
    print('    buy symbol value price E           -> extended market order')
    print('                                          (if possible otherwise create a job)')
    print('')
    print('')
    print('    price = MARKET_PRICE  [M]          -> buy at market price    (below mean if extended market order)')
    print('')
    print('    price = MEAN_PRICE    [m]          -> buy below mean')
    print('')
    print('    price = 100.0                      -> buy below 100.0')
    print('')
    print('')
    print('    Eg:')
    print('        value = 10k')
    print('        value = 192*10')
    print('        value = _               -> value saved in preferences')
    print('    Eg:')
    print('        price = M')
    print('        price = m')
    print('        price = 123')
    print('        price = -3%             <- -3% from the current realtime price')
    print('')


def action_buy(params, data):
    trade = data['trade']
    console = data['console']

    #
    symbol = params[0].strip().upper()
    value______ = string_to_value(params[1]) if params[1] != '_' else read_preferences(symbol, data['preferences'])[0]
    limit_price = string_to_price_relative(params[2], symbol, trade, condition='') if len(params) > 2 else 'MEAN_PRICE'
    session____ = string_to_session(params[3]) if len(params) > 3 else 'REGULAR'
    prev_order_id = string_to_int(params[4]) if len(params) > 4 else None
    order_term = 'GOOD_UNTIL_CANCEL'

    if value______ is None:
        return '-> error: value'
    if limit_price is None:
        return '-> error: limit_price'
    if session____ is None:
        return '-> error: session'

    #
    # previous orders
    #
    prev_order_id = select_from_open_orders(prev_order_id, symbol, 'BUY', trade, console)
    if prev_order_id == 'abort':
        return False

    #
    # amount, price, quantity
    #
    try:
        if isinstance(limit_price, float):
            price = limit_price
        else:
            price = trade.get_current_price(symbol)
            price = round(price, 2)
        quantity = int(math.floor(value______ / price))
    except ValueError as e:
        print(e)
        return False

    #
    # TODO check if I have money to make the purchase
    #

    #
    # market and immediate_order
    #
    limit_price, immediate_order = decide_market_limit_price(session____, limit_price, price)

    #
    # confirm
    #
    print(format_order_action('BUY', symbol, quantity, limit_price, session____, order_term, prev_order_id, immediate_order))
    yn = console.prompt_selection('confirm [y/n]? ', Console.str_from(['y', 'n']), default='n')
    if yn == 'n':
        return False

    #
    # order
    #
    if immediate_order:
        try:
            order_no, msg = trade.place_limit_order(action='BUY', symbol=symbol, quantity=quantity, limit_price=limit_price, session=session____, order_term=order_term, prev_order_id=prev_order_id)
        except ValueError as e:
            print(str(e))
            return False
        print(msg)
        print('order_no = ' + str(order_no))

    else:
        #
        # TODO Not fully tested.
        #
        job_server = data['job_server']
        new_id = job_server.next_valid_task_id()
        new_task = Tasks.OrderWhenOpen(new_id, None)

        new_task.order_data['action'] = 'BUY'
        new_task.order_data['symbol'] = symbol
        new_task.order_data['quantity'] = quantity
        new_task.order_data['limit_price'] = limit_price
        new_task.order_data['order_term'] = order_term
        new_task.order_data['prev_order_id'] = prev_order_id

        job_server.add(new_task)
        job_server.list_done_tasks()
        print('job created')
    return False


#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
def help_sell():
    print('')
    print('    sell symbol price R                ->          market order    (default)')
    print('    sell symbol price E                -> extended market order')
    print('                                          (if possible otherwise create a job)')
    print('')
    print('    price = MARKET_PRICE  [M]          -> sell at market price    (above mean if extended market order)')
    print('')
    print('    price = MEAN_PRICE    [m]          -> sell above mean')
    print('')
    print('    price = 100.0                      -> sell above 100.0')
    print('')
    print('')
    print('    Eg:')
    print('        price = M')
    print('        price = m')
    print('        price = 123')
    print('        price = +3%             <- +3% from the current price')
    print('')


def action_sell(params, data):
    trade = data['trade']
    console = data['console']

    #
    symbol = params[0].strip().upper()
    limit_price = string_to_price_relative(params[1], symbol, trade, condition='') if len(params) > 1 else 'MEAN_PRICE'
    session____ = string_to_session(params[2]) if len(params) > 2 else 'REGULAR'
    prev_order_id = string_to_int(params[3]) if len(params) > 3 else None
    order_term = 'GOOD_UNTIL_CANCEL'

    if limit_price is None:
        return '-> error: limit_price'
    if session____ is None:
        return '-> error: session'

    #
    # quantity
    #
    quantity = int(check_positions_quantity(symbol, data))
    if quantity <= 0:
        print('Cannot sell an equity that I do not own')
        return False

    #
    # previous orders
    #
    open_orders = trade.find_open_orders(symbol, 'SELL')
    if len(open_orders) > 1:
        print('Multiple sell orders have been placed on this security, please cancel them before continue.')
        return False
    if len(open_orders) == 1:
        if prev_order_id is not None:
            print('A sell order has already been placed [' + str(open_orders[0][0]) + '] on this security and it is not ' + str(prev_order_id))
            return False
        prev_order_id = open_orders[0][0]

    #
    # market and immediate_order
    #
    limit_price, immediate_order = decide_market_limit_price(session____, limit_price, None)

    #
    # confirm
    #
    print(format_order_action('SELL', symbol, quantity, limit_price, session____, order_term, prev_order_id, immediate_order))
    yn = console.prompt_selection('confirm [y/n]? ', Console.str_from(['y', 'n']), default='n')
    if yn == 'n':
        return False

    #
    # order
    #
    if immediate_order:
        try:
            order_no, msg = trade.place_limit_order(action='SELL', symbol=symbol, quantity=quantity, limit_price=limit_price, session=session____, order_term=order_term, prev_order_id=prev_order_id)
        except ValueError as e:
            print(str(e))
            return False
        print(msg)
        print('order_no = ' + str(order_no))

    else:
        #
        # TODO Not fully tested.
        #
        job_server = data['job_server']
        new_id = job_server.next_valid_task_id()
        new_task = Tasks.OrderWhenOpen(new_id, None)

        new_task.order_data['action'] = 'SELL'
        new_task.order_data['symbol'] = symbol
        new_task.order_data['quantity'] = quantity
        new_task.order_data['limit_price'] = limit_price
        new_task.order_data['order_term'] = order_term
        new_task.order_data['prev_order_id'] = prev_order_id

        job_server.add(new_task)
        job_server.list_done_tasks()
        print('job created')

    return False


#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
def help_trail():
    print('')
    print('    trail symbol margin                -> create a job')
    print('')
    print('    Eg:')
    print('         margin = -3%                  -> sell if below margin')
    print('')
    print('')


def action_sell_trailing(params, data):
    trade = data['trade']

    #
    symbol = params[0].strip().upper()
    margin = string_to_relative(params[1])
    prev_order_id = string_to_int(params[2]) if len(params) > 2 else None
    order_term = 'GOOD_UNTIL_CANCEL'

    if margin is None:
        return '-> error: margin'
    if margin >= 0:
        print('-> error: margin must be negative')
        return False

    #
    # quantity
    #
    quantity = int(check_positions_quantity(symbol, data))
    if quantity <= 0:
        print('Cannot sell an equity that I do not own')
        return False

    #
    # previous orders
    #
    open_orders = trade.find_open_orders(symbol, 'SELL')
    if len(open_orders) > 1:
        print('Multiple sell orders have been placed on this security, please cancel them before continue.')
        return False
    if len(open_orders) == 1:
        if prev_order_id is not None:
            print('A sell order has already been placed [' + str(open_orders[0][0]) + '] on this security and it is not ' + str(prev_order_id))
            return False
        prev_order_id = open_orders[0][0]

    #
    # TODO Not fully tested.
    #
    job_server = data['job_server']
    new_id = job_server.next_valid_task_id()
    new_task = Tasks.SellTrailing(new_id, None)

    new_task.set_order_data(symbol=symbol, qty=quantity, margin=margin, prev_order_id=prev_order_id, order_term=order_term, update_freq=10)

    job_server.add(new_task)
    job_server.list_done_tasks()
    print('job created')

    return False


#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
#####################################################################################################################################################
def help_sell_stop():
    print('')
    print('    protect symbol margin R            ->          market order    (default)')
    print('    protect symbol margin E            -> extended market order')
    print('                                          (if possible otherwise create a job)')
    print('')
    print('    Eg:')
    print('         margin = -3%                  -> sell if below margin')
    print('')
    print('')


def action_sell_stop(params, data):
    trade = data['trade']
    console = data['console']

    #
    symbol = params[0].strip().upper()
    margin = string_to_relative(params[1])
    session____ = string_to_session(params[2]) if len(params) > 2 else 'REGULAR'
    prev_order_id = string_to_int(params[3]) if len(params) > 3 else None
    order_term = 'GOOD_UNTIL_CANCEL'

    if margin is None:
        return '-> error: margin'
    if margin >= 0:
        print('-> error: margin must be negative')
        return False
    if session____ is None:
        return '-> error: session'

    #
    # quantity
    #
    quantity = int(check_positions_quantity(symbol, data))
    if quantity <= 0:
        print('Cannot sell an equity that I do not own')
        return False

    #
    # previous orders
    #
    old_stop_price = None
    open_orders = trade.find_open_orders(symbol, 'SELL')
    if len(open_orders) > 1:
        print('Multiple sell orders have been placed on this security, please cancel them before continue.')
        return False
    if len(open_orders) == 1:
        # save old price
        if open_orders[0][1]['priceType'] == 'STOP':
            if int(open_orders[0][1]['orderedQuantity']) == quantity:
                old_stop_price = float(open_orders[0][1]['stopPrice'])
        # check used prev_order_id
        if prev_order_id is not None:
            print('A sell order has already been placed [' + str(open_orders[0][0]) + '] on this security and it is not ' + str(prev_order_id))
            return False
        prev_order_id = open_orders[0][0]

    #
    # price
    #
    try:
        current_price = trade.get_current_price(symbol)
        stop_price = round(current_price * (1.0 + margin), 2)
    except ValueError as e:
        print(str(e))
        return False

    #
    # market and immediate_order
    #
    _, immediate_order = decide_market_limit_price(session____, None, None)

    #
    # confirm
    #
    if (old_stop_price is not None) and (old_stop_price > stop_price):
        current_set_margin = round(((old_stop_price / current_price) - 1.0) * 100.0, 2)
        print('protection already set to  ' + str(current_set_margin) + '%    (' + str(old_stop_price) + ').')
        return False
    print(format_order_action('SELL_STOP', symbol, quantity, stop_price, session____, order_term, prev_order_id, immediate_order))
    yn = console.prompt_selection('confirm [y/n]? ', Console.str_from(['y', 'n']), default='n')
    if yn == 'n':
        return False

    #
    # order
    #
    if immediate_order:
        try:
            order_no, msg = trade.place_stop_order(action='SELL', symbol=symbol, quantity=quantity, stop_price=stop_price, session=session____, order_term=order_term, prev_order_id=prev_order_id)
        except ValueError as e:
            print(str(e))
            return False
        print(msg)
        print('order_no = ' + str(order_no))

    else:
        #
        # TODO Not fully tested.
        #
        job_server = data['job_server']
        new_id = job_server.next_valid_task_id()
        new_task = Tasks.OrderWhenOpen(new_id, None)

        new_task.order_data['action'] = 'SELL_STOP'
        new_task.order_data['symbol'] = symbol
        new_task.order_data['quantity'] = quantity
        new_task.order_data['stop_price'] = stop_price
        new_task.order_data['order_term'] = order_term
        new_task.order_data['prev_order_id'] = prev_order_id

        job_server.add(new_task)
        job_server.list_done_tasks()
        print('job created')

    return False
