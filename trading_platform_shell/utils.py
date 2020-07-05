from typing import Optional, Union, List

from tabulate import tabulate

from interactive_shell import Console
from trade_interface import market_session


#
#
#
def format_order(o):
    element = [''] * 8
    element[0] = o['orderId']
    element[1] = o['orderAction']
    element[2] = o['symbol']
    element[3] = o['orderStatus']
    if o['orderStatus'] == 'EXECUTED':
        element[4] = '@'
        element[5] = str(o['executedPrice']) + '$'
        element[6] = '(' + str(o['filledQuantity']) + ')'
    if o['orderStatus'] == 'OPEN':
        element[4] = o['priceType']
        if o['priceType'] == 'LIMIT':
            element[5] = str(o['limitPrice']) + '$'
        if o['priceType'] == 'STOP':
            element[5] = str(o['stopPrice']) + '$'
        if o['priceType'] == 'STOP_LIMIT':
            element[5] = 'limit = ' + str(o['limitPrice']) + '$ ' + ' stop = ' + str(o['stopPrice']) + '$'
        element[6] = '(' + str(o['orderedQuantity']) + ')'
    return element


#
#
#
def select_from_open_orders(prev_order_id: int, symbol: str, action: str, trade, console) -> Union[Optional[int], str]:
    if prev_order_id is None:
        open_orders = trade.find_open_orders(symbol, action)
        if len(open_orders) >= 1:
            print('Open orders:')
            open_orders_formatted = [format_order(o[1]) for o in open_orders]
            print(tabulate(open_orders_formatted, stralign='left', tablefmt='plain'))
            if len(open_orders) == 1:
                yn = console.prompt_selection('Overwrite the existing order [y/n]? ', Console.str_from(['y', 'n']), default=None)
                if yn is None:
                    return 'abort'
                if yn == 'y':
                    prev_order_id = open_orders[0][0]
            else:
                open_orders_list = [o[0] for o in open_orders]
                prev_order_id = console.prompt_selection('Which order do you want to modify? ', Console.int_from(open_orders_list), default=None)
                if prev_order_id is None:
                    return 'abort'

    return prev_order_id


#
#
#
def check_positions_quantity(symbol: str, data) -> int:
    trade = data['trade']
    symbol = symbol.strip().upper()

    try:
        positions = trade.list_positions()
    except ValueError as e:
        print(str(e))
        return False

    quantity = 0
    for p in positions:
        if symbol == p[0]:
            quantity += p[1]

    return quantity


#
#
#
def decide_market_limit_price(session, limit_price, price):
    #
    # market
    #
    if session == 'REGULAR':
        # MARKET_PRICE
        # MEAN_PRICE
        # PRICE
        if limit_price == 'MEAN_PRICE' and (price is not None):
            limit_price = price
    else:
        # MEAN_PRICE
        # PRICE
        if limit_price == 'MARKET_PRICE':
            limit_price = 'MEAN_PRICE'
        if limit_price == 'MEAN_PRICE' and (price is not None):
            if market_session() != 'NO_TRADE':
                # in case of EXTENDED or REGULAR market
                limit_price = price

    #
    # immediate_order
    #
    if session == 'REGULAR' or market_session() != 'NO_TRADE':
        immediate_order = True
    else:
        immediate_order = False

    return limit_price, immediate_order


#
# list_order functions
#
def find_protections(order_data: dict, symbols: List[str], output: List[dict]) -> None:
    if order_data['orderStatus'] != 'OPEN':
        return
    if order_data['orderAction'] != 'SELL':
        return
    if (order_data['priceType'] != 'LIMIT') and (order_data['priceType'] != 'STOP') and (order_data['priceType'] != 'STOP_LIMIT'):
        return

    # find index
    index = None
    for i in range(len(symbols)):
        if symbols[i] == order_data['symbol']:
            index = i
            break
    if index is None:
        return

    # process
    if output[index] is None:
        output[index] = dict()

    if order_data['priceType'] == 'LIMIT':
        output[index]['LIMIT'] = {'price': float(order_data['limitPrice']), 'qty': int(float(order_data['orderedQuantity']))}

    if (order_data['priceType'] == 'STOP') or (order_data['priceType'] == 'STOP_LIMIT'):
        output[index]['STOP'] = {'price': float(order_data['stopPrice']), 'qty': int(float(order_data['orderedQuantity']))}

    return
