

#
#
#
def format_order_action(action, symbol, quantity, price, session, order_term, prev_order_id, immediate_order):
    session_ = 'REGULAR_HOURS' if session == 'REGULAR' else 'EXTENDED_HOURS'

    indicators = {'BUY': ' <= ', 'SELL': ' >= ', 'SELL_STOP': ' if <= ', 'BUY_STOP': ' if >= '}
    indicator = ' @ ' if price == 'MARKET_PRICE' else indicators[action]

    return action.ljust(5) + str(quantity).rjust(6) + ' ' + symbol.ljust(5) + indicator + str(price) + '      ' + session_ + '  ' + order_term + '  ' + (('CHANGE ORDER ' + str(prev_order_id)) if prev_order_id is not None else '') + ('' if immediate_order else '   -> Job')


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
    if o['multipleLegs']:
        element[7] = '    MULTIPLE LEGS'
    return element
