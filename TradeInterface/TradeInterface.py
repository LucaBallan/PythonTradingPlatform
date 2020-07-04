import random
import string
import threading
import time
import webbrowser
from typing import Tuple, List, Optional, Callable, Any, Sequence

from tabulate import tabulate

from TradeInterface.EtradeApi import EtradeApi, EtradeAuthorization
from TradeInterface.MarketSession import market_session
from TradeInterface.Utils import format_order_action


#
#
#
def synchronized():
    def wrap(f):
        def new_function(*args, **kwargs):
            lock = args[0].mutex
            lock.acquire()
            try:
                return f(*args, **kwargs)
            finally:
                lock.release()
        return new_function
    return wrap


#
#
#
class TradeInterface:
    mutex: threading.RLock
    _api: Optional[EtradeApi] = None
    _selected_account: Optional[str] = None

    #
    #
    #
    def __init__(self, keys: dict, use_sandbox: bool, browser_path: str):
        keys = keys['sandbox'] if use_sandbox else keys['production']
        self._consumer_key = keys['consumer_key']
        self._consumer_secret = keys['consumer_secret']
        self._browser_path = browser_path
        self.mutex = threading.RLock()
        self.__use_product_key = not use_sandbox

    #
    # TODO Not fully tested.
    #
    def __error_report(self, header: str, e: Any):
        if hasattr(e, 'response'):
            report = open('error_report.html', 'w')
            report.write(e.response.text)
            report.close()
            print(header + ': (see browser)')
            webbrowser.get(self._browser_path).open('error_report.html')
        else:
            print(header + ':' + e)
        return False

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
        oauth = EtradeAuthorization()

        # 1) get request token
        #    exp: 5 min
        try:
            verifier_url = oauth.get_request_token(self._consumer_key, self._consumer_secret)
        except Exception as e:
            return self.__error_report('connect', e)

        # 2) get verification code
        #
        if not webbrowser.get(self._browser_path).open(verifier_url, new=2):
            return False

        # 3) copy verification code
        #
        verifier_code = input('verifier_code = ')
        if verifier_code.strip() == '':
            return False

        # 4) get access token
        #    exp: midnight US Eastern time
        try:
            tokens = oauth.get_access_token(verifier_code)
        except Exception as e:
            return self.__error_report('connect', e)

        # 5) start session
        try:
            session = oauth.get_session(self._consumer_key, self._consumer_secret, tokens)
        except Exception as e:
            return self.__error_report('connect', e)

        self._api = EtradeApi(session=session, use_product_key=self.__use_product_key)
        return True

    #
    #
    #
    @synchronized()
    def disconnect(self) -> bool:
        if self._api is None:
            return True
        try:
            self._api.revoke_access_token()
            return True
        except Exception as e:
            print('disconnect: ' + str(e))
            return False

    #
    #
    #
    @synchronized()
    def select_account(self) -> None:
        """Asks user to select an account."""
        try:
            accounts = self._api.list_accounts()
            print(tabulate(accounts, headers=['', 'Id', 'Desc', 'Key'], stralign='center'))
            selection = None
            while True:
                try:
                    selection = int(float(input('select > ')))
                    if 0 <= selection < len(accounts):
                        break
                except ValueError:
                    continue
            self._selected_account = accounts[selection][3]
        except KeyError:
            raise ValueError('select_account: wrong response format.')
        except Exception as e:
            raise ValueError('select_account: ' + str(e))

    #
    #
    #
    @synchronized()
    def get_account_balance(self) -> Tuple[float, float, float]:
        """Retrieves account balance.

        Returns:
            Total account value
            Amount of cash available for investment
            Amount of cash not settled
        """
        try:
            return self._api.get_account_balance(account_id=self._selected_account)
        except KeyError:
            raise ValueError('get_account_balance: wrong response format.')
        except Exception as e:
            raise ValueError('get_account_balance: ' + str(e))

    #
    #
    #
    @synchronized()
    def list_positions(self) -> List[Tuple[str, float, float, float]]:
        """Retrieves all account positions.

        Returns:
            A list of (symbol, qty, currentPrice, costBasis)
        """
        try:
            out = self._api.get_account_positions(account_id=self._selected_account)
            return out
        except KeyError:
            raise ValueError('list_positions: wrong response format.')
        except Exception as e:
            raise ValueError('list_positions: ' + str(e))

    #
    #
    #
    @synchronized()
    def get_quote(self, symbols: Sequence[str],
                  only_intraday_data: bool = False) -> List[EtradeApi.QuoteData]:
        """Retrieves quote information.

        Args:
            symbols: List of symbols to retrieve.
            only_intraday_data: Boolean indicating if the only intraday data has to be retrieve.

        Returns:
            A list of QuoteData where QuoteData = (symbol, symbol_data).
            Symbol_data contains:
                intraday: 'ask', 'bid', 'high', 'low', 'lastTrade', 'totalVolume'
                all:      'askSize', 'bidSize', 'eps', 'estEarnings', 'dividend', 'symbolDescription'
        """
        symbols = [symbol.upper().strip() for symbol in symbols]
        try:
            quote = self._api.get_quote(symbols, only_intraday_data=only_intraday_data)
        except KeyError:
            raise ValueError('get_quote: wrong response format.')
        except Exception as e:
            raise ValueError('get_quote: ' + str(e))

        # Check if it retrieve all and only the requested symbols.
        if self.__use_product_key:
            if len(quote) != len(symbols):
                raise ValueError('get_quote: some requested quotes are missing.')
            for q in quote:
                if q[0] not in symbols:
                    raise ValueError('get_quote: some requested quotes are missing.')
        return quote

    #
    #
    #
    def get_current_price(self, symbol: str) -> float:
        """Retrieves price information.

        Args:
            symbol: Symbol to retrieve.

        Returns:
            The average price for the symbol.
        """
        quote = self.get_quote([symbol], only_intraday_data=True)[0][1]
        price = (quote['bid'] + quote['ask']) / 2.0
        if price == 0.0:
            raise ValueError('get_current_price: quote price is 0.')
        return price

    #
    # TODO Not fully tested.
    #
    def get_current_price_multi(self, symbols: Sequence[str]) -> List[Optional[float]]:
        """Retrieves price information.

        Args:
            symbols: Symbols to retrieve.

        Returns:
            The average prices for each symbols.
        """
        price = [None] * len(symbols)
        quote = self.get_quote(symbols, only_intraday_data=True)
        for i in range(len(symbols)):
            for q in quote:
                if q[0] == symbols[i]:
                    price[i] = (float(q[1]['bid']) + float(q[1]['ask'])) / 2.0
                    if price[i] == 0.0:
                        raise ValueError('get_current_price_multi: quote price is 0.')
                    break
        return price

    #
    #
    #
    @synchronized()
    def _parse_orders(self, f: Callable[[dict], bool]) -> None:
        request_orders = 25
        marker = None

        order_ids = set()
        while True:
            try:
                order_list, marker = self._api.list_orders(account_id=self._selected_account,
                                                           count=request_orders, marker=marker)
            except KeyError:
                raise ValueError('_parse_orders: wrong response format.')
            except Exception as e:
                raise ValueError('_parse_orders: ' + str(e))

            # Parse order list.
            for order in order_list:
                if order['orderId'] not in order_ids:
                    order_ids.add(order['orderId'])
                    if f(order):
                        return

            # Next batch.
            if marker is None:
                break
            time.sleep(0.5)  # TODO This value can be reduced.
            marker += request_orders

    #
    #
    #
    def list_orders(self) -> Sequence[dict]:
        """Retrieves all orders.

        Returns:
            List of all orders.
        """
        order_list = []

        def f(order: dict):
            order_list.append(order)
            return False

        self._parse_orders(f)
        return tuple(order_list)

    #
    #
    #
    def check_order_status(self, order_id: int) -> Optional[str]:
        """Checks order status.

        Args:
            order_id: Id of the order.

        Returns:
            Order status.
        """
        order_status = None

        def f(order: dict):
            nonlocal order_status
            if order['orderId'] == order_id:
                order_status = order['orderStatus']
                return True
            return False

        self._parse_orders(f)
        return order_status

    #
    #
    #
    def find_open_orders(self, symbol: str, action: str) -> List[Tuple[int, dict]]:
        """Retrieves all open orders for a specific symbol and a specific action.

        Args:
            symbol: Symbol to retrieve.
            action: Action BUY or SELL.

        Returns:
            List of orders.
        """
        order_list = []

        def f(order: dict):
            if order['symbol'] != symbol:
                return False
            if order['orderAction'] != action:
                return False
            if order['orderStatus'] != 'OPEN':
                return False
            order_list.append((order['orderId'], order))
            return False

        self._parse_orders(f)
        return order_list

    #
    #
    #
    def parse_all_orders(self, order_function: Callable[[dict], None]) -> None:
        """Parses all order with function order_function.

        Args:
            order_function: Function that parse each order.

        Returns:
            None
        """
        def f(order: dict):
            order_function(order)
            return False

        self._parse_orders(f)

    #
    #
    #
    @synchronized()
    def cancel_order(self, order_id: int) -> str:
        """Cancels an order.

        Args:
            order_id: Id of the order to cancel.

        Returns:
            Confirmation message.
        """
        try:
            res_msg = self._api.cancel_order(account_id=self._selected_account,
                                             order_id=order_id)
        except KeyError:
            raise ValueError('cancel_order: wrong response format.')
        except Exception as e:
            raise ValueError('cancel_order: ' + str(e))
        return res_msg

    #
    # TODO Not fully tested.
    #
    @synchronized()
    def place_limit_order(self,
                          action: str,
                          symbol: str,
                          quantity: int,
                          limit_price: float,
                          session: str,
                          prev_order_id: Optional[int],
                          order_term: str = 'GOOD_UNTIL_CANCEL') -> Tuple[int, str]:
        """
            limit_price    =   MARKET_PRICE     -> market value order                            (if EXTENDED -> MEAN)
                               MEAN_PRICE       -> limit at mean of bid and ask
                               value            -> limit at price
            prev_order_id  =   change a previous order
        """
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
                raise ValueError('market is not open.')
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
            msg = format_order_action(action, symbol, quantity, limit_price, session, order_term,
                                      prev_order_id, True)
            if limit_price == 'MARKET_PRICE':
                order_num = self._api.place_equity_order(accountId=self._selected_account,
                                                         symbol=symbol,
                                                         orderAction=action,
                                                         clientOrderId=client_order_id,
                                                         priceType='MARKET',
                                                         quantity=quantity,
                                                         marketSession=session,
                                                         orderTerm=order_term,
                                                         prev_order_id=prev_order_id)
            else:
                order_num = self._api.place_equity_order(accountId=self._selected_account,
                                                         symbol=symbol,
                                                         orderAction=action,
                                                         clientOrderId=client_order_id,
                                                         priceType='LIMIT',
                                                         limitPrice=limit_price,
                                                         quantity=quantity,
                                                         marketSession=session,
                                                         orderTerm=order_term,
                                                         prev_order_id=prev_order_id)
        except KeyError:
            raise ValueError('place_limit_order: wrong response format.')
        except Exception as e:
            raise ValueError('place_limit_order: ' + str(e))

        return order_num, msg

    #
    # TODO Not fully tested.
    #
    @synchronized()
    def place_stop_order(self,
                         action: str,
                         symbol: str,
                         quantity: int,
                         stop_price: float,
                         session: str,
                         prev_order_id: int,
                         order_term: str = 'GOOD_UNTIL_CANCEL') -> Tuple[int, str]:
        """
            stop_price     =   value      -> actual value
            prev_order_id  =   change a previous order
        """
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
                raise ValueError('market is not open.')

        #
        #
        #
        try:
            msg = format_order_action(action + '_STOP', symbol, quantity, stop_price, session, order_term,
                                      prev_order_id, True)
            order_num = self._api.place_equity_order(accountId=self._selected_account,
                                                     symbol=symbol,
                                                     orderAction=action,
                                                     clientOrderId=client_order_id,
                                                     priceType='STOP',
                                                     stopPrice=stop_price,
                                                     quantity=quantity,
                                                     marketSession=session,
                                                     orderTerm=order_term,
                                                     prev_order_id=prev_order_id)
        except KeyError:
            raise ValueError('place_stop_order: wrong response format.')
        except Exception as e:
            raise ValueError('place_stop_order: ' + str(e))

        return order_num, msg
