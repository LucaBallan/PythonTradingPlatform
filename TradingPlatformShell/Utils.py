import time
from typing import Optional, Union
from tabulate import tabulate
from InteractiveShell import Console
from TradeInterface import format_order, market_session


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

    request_orders = 25
    marker = 0
    while True:
        try:
            positions = trade.list_positions(count=request_orders, marker=marker)
        except ValueError as e:
            print(str(e))
            return False

        quantity = 0
        for p in positions:
            if symbol == p[0]:
                quantity += p[1]
        if len(positions) < request_orders:
            break
        time.sleep(0.5)
        marker += request_orders

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
