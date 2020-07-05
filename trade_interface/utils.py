

def format_order_action(action: str,
                        symbol: str,
                        quantity: float,
                        price: float,
                        session: str,
                        order_term: str,
                        prev_order_id: int,
                        immediate_order: bool) -> str:
    """Converts order request into human readable string."""

    session_ = 'REGULAR_HOURS' if session == 'REGULAR' else 'EXTENDED_HOURS'
    indicators = {'BUY': ' <= ', 'SELL': ' >= ', 'SELL_STOP': ' if <= ', 'BUY_STOP': ' if >= '}
    indicator = ' @ ' if price == 'MARKET_PRICE' else indicators[action]
    return (action.ljust(11) + str(quantity).rjust(8) + ' ' + symbol.ljust(5) + indicator +
            str(price) + '      ' + session_ + '  ' + order_term + '  ' +
            (('CHANGE ORDER ' + str(prev_order_id)) if prev_order_id is not None else '') +
            ('' if immediate_order else '   -> Job'))
