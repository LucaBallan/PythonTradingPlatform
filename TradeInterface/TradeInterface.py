from typing import Tuple, List, Optional
import webbrowser
import random
import string
import threading
import time
import json
from tabulate import tabulate
from requests_oauthlib import OAuth1Session
from TradeInterface.LowLevelEtradeApi import LowLevelEtradeApi, LowLevelEtradeAuthorization
from TradeInterface.MarketSession import market_session
from TradeInterface.Utils import format_order_action


#
#
#
def synchronized():
    def wrap(f):
        def new_function(*args, **kw):
            lock = args[0].mutex
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()

        return new_function
    return wrap


#
#
#
class TradeInterface:
    consumer_key = None
    consumer_secret = None
    verifier_code = None
    tokens = None
    dev = None

    # objects
    session = None
    low_level_api = None
    selected_account = None

    # others
    browser_path = None
    mutex = None

    #
    #
    #
    def __init__(self, keys, dev, browser_path):
        keys = keys['sandbox'] if dev else keys['production']
        self.consumer_key = keys['consumer_key']
        self.consumer_secret = keys['consumer_secret']
        self.browser_path = browser_path
        self.mutex = threading.RLock()         # blocks only other threads
        self.dev = dev

    #
    #
    #
    def __error_report(self, e):
        if hasattr(e, 'response'):
            report = open('error_report.html', 'w')
            report.write(e.response.text)
            report.close()
            webbrowser.get(self.browser_path).open('error_report.html')
        else:
            print(e)
        return False

    #
    #
    #
    @staticmethod
    def __get_error(error):
        if hasattr(error, 'response'):
            try:
                message = json.loads(error.response.text)
                return message['Error']['message']
            except Exception:
                return str(error.response.text)
        else:
            return str(error)

    #
    #
    #
    def __create_session(self) -> None:
        if self.session is None:
            self.session = OAuth1Session(self.consumer_key, self.consumer_secret, self.tokens['oauth_token'], self.tokens['oauth_token_secret'], signature_type='AUTH_HEADER')
            self.low_level_api = LowLevelEtradeApi(self.session)

    #
    #
    #
    @staticmethod
    def __gen_unique_id() -> str:
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

    #
    #
    #
    @synchronized()
    def connect(self) -> bool:
        oauth = LowLevelEtradeAuthorization()

        # 1) get request token
        #    exp: 5 min
        try:
            verifier_url = oauth.get_request_token(self.consumer_key, self.consumer_secret)
        except Exception as e:
            return self.__error_report(e)

        # 2) get verification code
        #
        if not webbrowser.get(self.browser_path).open(verifier_url, new=2):
            return False

        # 3) copy verification code
        #
        self.verifier_code = input('verifier_code = ')
        if self.verifier_code.strip() == '':
            return False

        # 4) get access token
        #    exp: midnight US Eastern time
        try:
            self.tokens = oauth.get_access_token(self.verifier_code)
        except Exception as e:
            return self.__error_report(e)

        return True

    #
    #
    #
    @synchronized()
    def disconnect(self) -> bool:
        self.__create_session()
        try:
            self.low_level_api.revoke_access_token()
            return True
        except Exception as e:
            print(self.__get_error(e))

    #
    #
    #
    @synchronized()
    def select_account(self) -> None:
        self.__create_session()

        try:

            accounts = self.low_level_api.list_accounts(dev=self.dev)
            print(tabulate(accounts, headers=['', 'Id', 'Desc', 'Value (K)'], stralign='center'))

            while True:
                try:
                    selection = int(float(input('select > ')))
                    if 0 <= selection < len(accounts):
                        break
                except ValueError:
                    continue

            self.selected_account = accounts[selection][1]

        except KeyError:
            raise ValueError('select_account: wrong response format')
        except Exception as e:
            raise ValueError('select_account: ' + self.__get_error(e))

    #
    #
    #
    @synchronized()
    def get_account_balance(self) -> Tuple[float, float, float]:
        """
        :return: netAccountValue, settledCashForInvestment, unSettledCashForInvestment
        """
        self.__create_session()

        try:
            return self.low_level_api.get_account_balance(account_id=self.selected_account, dev=self.dev)

        except KeyError:
            raise ValueError('get_account_balance: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))

    #
    #
    #
    @synchronized()
    def list_positions(self, count=25, marker=0) -> List[Tuple[str, int, float, float]]:
        """
        :return: [symbol, qty, currentPrice, costBasis]
        """
        self.__create_session()
        try:
            out = self.low_level_api.get_account_positions(account_id=self.selected_account, count=count, marker=marker, dev=self.dev)
            return out
        except KeyError:
            raise ValueError('list_positions: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))

    #
    #
    #
    @synchronized()
    def cancel_order(self, order_id) -> str:
        """
        :return: result message
        """
        self.__create_session()
        try:
            out = self.low_level_api.cancel_order(account_id=self.selected_account, order_num=order_id, dev=self.dev)
            return out
        except KeyError:
            raise ValueError('cancel_order: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))

    #
    #
    #
    @synchronized()
    def get_quote(self, symbols, intraday=False) -> List[Tuple[str, dict]]:
        self.__create_session()
        symbols = [symbol.upper().strip() for symbol in symbols]

        try:

            quote = self.low_level_api.get_quote(symbols, intraday=intraday, dev=self.dev)

        except KeyError:
            raise ValueError('get_quote: wrong response format')
        except Exception as e:
            raise ValueError(str(e))

        if not self.dev:
            if len(quote) != len(symbols):
                raise ValueError('get_quote: incomplete response')
            for q in quote:
                if q[0] not in symbols:
                    raise ValueError('get_quote: ' + q[0] + ' not requested')

        # fix market close
        for q in quote:
            if q[1]['bid'] == 0 and q[1]['ask'] == 0:
                q[1]['ask'] = float(q[1]['lastTrade'])
                q[1]['bid'] = float(q[1]['lastTrade'])

        return quote

    #
    #
    #
    @synchronized()
    def list_orders(self, count=25, marker=None) -> Tuple[List[dict], Optional[str], int]:
        self.__create_session()
        try:
            out, next_marker, not_parsed = self.low_level_api.list_orders(account_id=self.selected_account, count=count, marker=marker, dev=self.dev)
            return out, next_marker, not_parsed
        except KeyError:
            raise ValueError('list_orders: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))

    #
    #
    #
    def check_order_status(self, order_id) -> Optional[str]:
        request_orders = 25
        marker = None
        while True:
            try:
                order_list, marker, _ = self.list_orders(count=request_orders, marker=marker)
            except Exception as e:
                raise ValueError(self.__get_error(e))

            for o in order_list:
                if int(o['orderId']) == order_id:
                    return o['orderStatus']
            if marker is None:
                break
            time.sleep(0.5)
            marker += request_orders
        return None

    #
    #
    #
    def find_open_orders(self, symbol: str, action: str) -> List[Tuple[int, dict]]:
        request_orders = 25
        marker = None

        orders = []
        while True:
            try:
                order_list, marker, _ = self.list_orders(count=request_orders, marker=marker)
            except Exception as e:
                raise ValueError(self.__get_error(e))

            for o in order_list:
                if o['symbol'] != symbol:
                    continue
                if o['orderAction'] != action:
                    continue
                if o['orderStatus'] != 'OPEN':
                    continue
                orders.append((int(o['orderId']), o))
            if marker is None:
                break
            time.sleep(0.5)
            marker += request_orders
        return orders

    #
    #
    #
    @synchronized()
    def get_current_price(self, symbol: str) -> float:
        """
        :return: quote price
        """
        try:
            quote = self.get_quote([symbol], intraday=True)[0][1]
        except ValueError as e:
            raise e
        price = (float(quote['bid']) + float(quote['ask'])) / 2.0
        if price == 0.0:
            raise ValueError('quote price is 0')
        return price

    #
    #
    #
    @synchronized()
    def place_limit_order(self, action: str, symbol: str, quantity: int, limit_price: float, session: str, prev_order_id: int, order_term: str='GOOD_UNTIL_CANCEL') -> Tuple[int, str]:
        """
            limit_price    =   MARKET_PRICE     -> market value order                            (if EXTENDED -> MEAN)
                               MEAN_PRICE       -> limit at mean of bid and ask
                               value            -> limit at price
            prev_order_id  =   change a previous order
        """
        self.__create_session()

        #
        #
        #
        client_order_id = self.__gen_unique_id()
        symbol = symbol.upper().strip()
        quantity = int(quantity)
        order_term = order_term.upper().strip()
        session = session.upper().strip()

        #
        # market
        #
        m_session = market_session()
        if session == 'EXTENDED':
            if m_session == 'NO_TRADE':
                raise ValueError('market is not open')
            if limit_price == 'MARKET_PRICE':
                limit_price = 'MEAN_PRICE'

        #
        # limit_price
        #
        if limit_price == 'MEAN_PRICE':
            limit_price = self.get_current_price(symbol)
            limit_price = round(limit_price, 2)

        #
        #
        #
        try:
            msg = format_order_action(action, symbol, quantity, limit_price, session, order_term, prev_order_id, True)
            if limit_price == 'MARKET_PRICE':
                order_num = self.low_level_api.place_equity_order(dev=self.dev, accountId=self.selected_account, symbol=symbol, orderAction=action, clientOrderId=client_order_id,
                                                                  priceType='MARKET', quantity=quantity, marketSession=session, orderTerm=order_term,
                                                                  prev_order_id=prev_order_id)
            else:
                order_num = self.low_level_api.place_equity_order(dev=self.dev, accountId=self.selected_account, symbol=symbol, orderAction=action, clientOrderId=client_order_id,
                                                                  priceType='LIMIT', limitPrice=limit_price, quantity=quantity, marketSession=session, orderTerm=order_term,
                                                                  prev_order_id=prev_order_id)

            return order_num, msg
        except KeyError:
            raise ValueError('place_equity_order: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))

    #
    #
    #
    @synchronized()
    def place_stop_order(self, action: str, symbol: str, quantity: int, stop_price: float, session: str, prev_order_id: int, order_term: str='GOOD_UNTIL_CANCEL') -> Tuple[int, str]:
        """
            stop_price     =   value      -> actual value
            prev_order_id  =   change a previous order
        """
        self.__create_session()

        #
        #
        #
        client_order_id = self.__gen_unique_id()
        symbol = symbol.upper().strip()
        quantity = int(quantity)
        order_term = order_term.upper().strip()
        session = session.upper().strip()
        stop_price = round(stop_price, 2)

        #
        # market
        #
        m_session = market_session()
        if session == 'EXTENDED':
            if m_session == 'NO_TRADE':
                raise ValueError('market is not open')

        #
        #
        #
        try:
            msg = format_order_action(action + '_STOP', symbol, quantity, stop_price, session, order_term, prev_order_id, True)
            order_num = self.low_level_api.place_equity_order(dev=self.dev, accountId=self.selected_account, symbol=symbol, orderAction=action, clientOrderId=client_order_id,
                                                              priceType='STOP', stopPrice=stop_price, quantity=quantity, marketSession=session, orderTerm=order_term,
                                                              prev_order_id=prev_order_id)

            return order_num, msg
        except KeyError:
            raise ValueError('place_equity_order: wrong response format')
        except Exception as e:
            raise ValueError(self.__get_error(e))
