

#
#
#
def string_to_value(s):
    s = s.strip().lower()
    if s[-1] == 'k':
        try:
            value = float(s[:-1])
            return value * 1000.0
        except ValueError:
            return None
    try:
        value = float(s)
        return value
    except ValueError:
        pass
    try:
        return float(eval(s))
    except Exception:
        pass
    return None


#
#
#
def string_to_price(s):
    s = s.strip()
    if s == '' or s == 'm':
        return 'MEAN_PRICE'
    if s == 'M':
        return 'MARKET_PRICE'
    if s.upper() == 'MARKET_PRICE':
        return 'MARKET_PRICE'
    try:
        num = float(s)
        return round(num, 2)
    except ValueError:
        return None


#
#
#
def string_to_relative(s):
    if s[-1] != '%':
        return None
    try:
        margin = float(s[:-1])
    except ValueError:
        return None
    return margin / 100.0


#
#
#
def string_to_price_relative(s, symbol, trade, condition='negative'):
    price = string_to_price(s)
    if price is not None:
        return price

    margin = string_to_relative(s)
    if margin is None:
        return None

    if condition == 'negative':
        if margin >= 0:
            print('% must be negative')
            return None
    if condition == 'positive':
        if margin <= 0:
            print('% must be positive')
            return None

    try:
        price = trade.get_current_price(symbol)
    except ValueError as e:
        print(str(e))
        return None

    return round(price * (1.0 + margin), 2)


#
#
#
def string_to_int(s):
    try:
        num = int(float(s))
        return num
    except ValueError:
        return None


#
#
#
def string_to_session(s):
    s = s.strip()
    if s == '' or s == 'R':
        return 'REGULAR'
    if s == 'E':
        return 'EXTENDED'
    return None


#
#
#
def string_to_price_or_quote_price(s, trade):
    s = s.strip().lower()
    try:
        value = float(s)
        return value, False
    except ValueError:
        pass
    try:
        return float(eval(s)), False
    except Exception as _:
        pass
    if s[-1] == '%':
        return None, False
    try:
        value = trade.get_current_price(s)
        return value, True
    except ValueError as e:
        print('quote request for ' + s.upper() + ': ' + str(e))
        pass
    return None, False
