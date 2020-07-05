from typing import Tuple, List, Optional, Union, Any, Sequence, Dict

import xmltodict
from requests_oauthlib import OAuth1Session, requests


#
#
#
class EtradeAuthorization:
    def __init__(self):
        self.__auth_session = None

    def get_request_token(self, consumer_key: str, consumer_secret: str) -> str:
        self.__auth_session = OAuth1Session(consumer_key, consumer_secret, callback_uri='oob', signature_type='AUTH_HEADER')
        self.__auth_session.fetch_request_token('https://api.etrade.com/oauth/request_token')
        authorization_url = self.__auth_session.authorization_url('https://us.etrade.com/e/t/etws/authorize')
        a_key = self.__auth_session.parse_authorization_response(authorization_url)
        return '%s?key=%s&token=%s' % ('https://us.etrade.com/e/t/etws/authorize', consumer_key, a_key['oauth_token'])

    def get_access_token(self, verifier: str) -> dict:
        return self.__auth_session.fetch_access_token('https://api.etrade.com/oauth/access_token', verifier=verifier)

    @staticmethod
    def get_session(consumer_key: str, consumer_secret: str, tokens: dict) -> OAuth1Session:
        return OAuth1Session(consumer_key, consumer_secret, tokens['oauth_token'],
                             tokens['oauth_token_secret'], signature_type='AUTH_HEADER')


#
#
#
class EtradeApi:
    QuoteData = Tuple[str, Dict[str, float]]

    #
    #
    #
    def __init__(self, session: OAuth1Session, use_product_key: bool):
        self.__use_product_key = use_product_key
        self.__base_url_dev = 'https://apisb.etrade.com/v1/'
        self.__base_url_prod = 'https://api.etrade.com/v1/'
        self.__session = session

    #
    #
    #
    def revoke_access_token(self) -> None:
        """Revokes access token."""
        resp = self.__session.get('https://api.etrade.com/oauth/revoke_access_token')
        resp.raise_for_status()
        resp = xmltodict.parse(resp.text)
        if 'Error' in resp:          # TODO Not fully tested.
            raise ValueError(resp['Error']['message'])

    #
    #
    #
    def __get_url(self, command: str = '') -> str:
        if self.__use_product_key:
            return self.__base_url_prod + command
        else:
            return self.__base_url_dev + command

    #
    #
    #
    @staticmethod
    def __to_list(list_or_object: Union[Sequence, Any]) -> List[Any]:
        if isinstance(list_or_object, list):
            return list_or_object
        if isinstance(list_or_object, tuple):
            return list(list_or_object)
        return [list_or_object]

    #
    #
    #
    def get_account_balance(self, account_id: str) -> Tuple[float, float, float]:
        """Retrieves account balance.

        Args:
            account_id: Id of the account where the request has to be performed.

        Returns:
            Total account value
            Amount of cash available for investment
            Amount of cash not settled
        """
        api_url = self.__get_url('accounts/' + account_id + '/balance?instType=BROKERAGE&realTimeNAV=true')
        resp = self.__session.get(api_url)

        info = self.__retrieve_response(resp)
        info = info['BalanceResponse']['Computed']
        return (float(info['RealTimeValues']['totalAccountValue']),
                float(info['settledCashForInvestment']),
                float(info['unSettledCashForInvestment']))

    #
    #
    #
    def list_accounts(self) -> List[Tuple[int, int, str, str]]:
        """Lists all available accounts.

        Returns:
            A list of (account number, account id, account description, account key)
        """
        api_url = self.__get_url('accounts/list')
        resp = self.__session.get(api_url)

        accounts = self.__retrieve_response(resp)
        accounts = self.__to_list(accounts['AccountListResponse']['Accounts']['Account'])
        accounts = [(i, accounts[i]['accountId'], accounts[i]['accountDesc'], accounts[i]['accountIdKey']) for i in range(len(accounts))]
        return accounts

    #
    #
    #
    def get_account_positions(self, account_id: str) -> List[Tuple[str, float, float, float]]:
        """Retrieves all account positions.

        Args:
            account_id: Id of the account where the request has to be performed.

        Returns:
            A list of (symbol, qty, currentPrice, costBasis)
        """
        # TODO Paging is not implemented.
        api_url = self.__get_url('accounts/' + str(account_id) + '/portfolio')
        resp = self.__session.get(api_url)

        positions = self.__retrieve_response(resp)
        positions = self.__to_list(positions['PortfolioResponse']['AccountPortfolio']['Position'])
        positions = [(
            p['Product']['symbol'].strip().upper(),
            float(p['quantity']),
            float(p['marketValue']) / float(p['quantity']),
            float(p['totalCost'])) for p in positions]
        return positions

    #
    #
    #
    @staticmethod
    def __format_quote(data: dict, label: str) -> Dict[str, float]:
        export_data = {'ask': float(data['ask']),
                       'bid': float(data['bid']),
                       'high': float(data['high']),
                       'low': float(data['low']),
                       'lastTrade': float(data['lastTrade']),
                       'totalVolume': float(data['totalVolume'])}
        if export_data['bid'] == 0 and export_data['ask'] == 0:
            export_data['ask'] = export_data['lastTrade']
            export_data['bid'] = export_data['lastTrade']
        if label == 'All':
            export_data['askSize'] = float(data['askSize'])
            export_data['bidSize'] = float(data['bidSize'])
            export_data['eps'] = float(data['eps'])
            export_data['estEarnings'] = float(data['estEarnings'])
            export_data['dividend'] = float(data['dividend'])
            export_data['symbolDescription'] = data['symbolDescription']
        return export_data

    #
    #
    #
    def get_quote(self, symbols: Sequence[str], only_intraday_data: bool) -> List[QuoteData]:
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
        if len(symbols) > 25:
            raise ValueError('get_quote: Too many symbols to quote.')

        api_url = self.__get_url('market/quote/' + ','.join(symbols))
        params = {'detailFlag': 'ALL'} if not only_intraday_data else {'detailFlag': 'INTRADAY'}
        resp = self.__session.get(api_url, params=params)

        data = self.__retrieve_response(resp)
        data = data['QuoteResponse']['QuoteData']
        label = 'All' if not only_intraday_data else 'Intraday'
        if isinstance(data, dict):
            return [(data['Product']['symbol'], self.__format_quote(data[label], label))]
        else:
            return [(x['Product']['symbol'], self.__format_quote(x[label], label)) for x in data]

    #
    #
    #
    def list_orders(self, account_id: str, count: int, marker: Optional[int]) -> Tuple[Sequence[dict], Optional[int]]:
        """Retrieves all orders.

        Args:
            account_id: Id of the account where the request has to be performed.
            count: Number of orders to retrieve.
            marker: Marker of the first order to retrieve.

        Returns:
            order_data: List of orders.
            current_marker: Next marker.
        """
        api_url = self.__get_url('accounts/' + account_id + '/orders')

        params = {'count': count}
        if marker is not None:
            params['marker'] = marker

        resp = self.__session.get(api_url, params=params)

        resp = self.__retrieve_response(resp)
        resp = resp['OrdersResponse']
        current_marker = None
        if 'marker' in resp:
            if len(resp['marker']) != 0:
                current_marker = int(resp['marker'])
        order_list = self.__to_list(resp['Order'])

        order_data = []
        for o in order_list:
            order_info = {'orderId': int(o['orderId'])}
            o = o['OrderDetail']
            order_info['orderStatus'] = o['status']
            order_info['symbol'] = o['Instrument']['Product']['symbol']
            order_info['orderAction'] = o['Instrument']['orderAction']
            order_info['orderedQuantity'] = o['Instrument']['orderedQuantity']
            order_info['orderTerm'] = o['orderTerm']
            order_info['marketSession'] = o['marketSession']
            if order_info['orderStatus'] == 'EXECUTED':
                order_info['executedPrice'] = o['Instrument']['averageExecutionPrice']
                order_info['filledQuantity'] = o['Instrument']['filledQuantity']
            if order_info['orderStatus'] == 'OPEN':
                order_info['priceType'] = o['priceType']
                if order_info['priceType'] == 'LIMIT':
                    order_info['limitPrice'] = o['limitPrice']
                if order_info['priceType'] == 'STOP':
                    order_info['stopPrice'] = o['stopPrice']
                if order_info['priceType'] == 'STOP_LIMIT':
                    order_info['limitPrice'] = o['limitPrice']
                    order_info['stopPrice'] = o['stopPrice']
            order_data.append(order_info)

        return order_data, current_marker

    #
    #
    #
    @staticmethod
    def __check_order(**kwargs) -> None:
        mandatory = [
            'accountId',
            'symbol',
            'orderAction',
            'clientOrderId',
            'priceType',
            'quantity',
            'orderTerm',
            'marketSession',
        ]
        if not all(param in kwargs for param in mandatory):
            raise ValueError('__check_order: input parameters missing.')

        if kwargs['priceType'] == 'STOP' and 'stopPrice' not in kwargs:
            raise ValueError('__check_order: stopPrice missing.')
        if kwargs['priceType'] == 'LIMIT' and 'limitPrice' not in kwargs:
            raise ValueError('__check_order: limitPrice missing.')
        if (kwargs['priceType'] == 'STOP_LIMIT'
                and 'limitPrice' not in kwargs
                and 'stopPrice' not in kwargs):
            raise ValueError('__check_order: stopPrice or limitPrice missing.')

    #
    #
    #
    @staticmethod
    def __build_order_payload(order_type: str, **kwargs) -> dict:
        instrument = {
            'Product': {'securityType': 'EQ',
                        'symbol': kwargs['symbol']},
            'orderAction': kwargs['orderAction'],
            'quantityType': 'QUANTITY',
            'quantity': int(kwargs['quantity']),  # TODO Force convertion to integer.
        }
        order = kwargs
        order['Instrument'] = instrument
        payload = {
            order_type: {
                'orderType': 'EQ',
                'clientOrderId': kwargs['clientOrderId'],
                'Order': order,
            }
        }
        if 'previewId' in kwargs:
            payload[order_type]['PreviewIds'] = {'previewId': kwargs['previewId']}
        return payload

    #
    #
    #
    @staticmethod
    def __retrieve_response(resp: requests.models.Response) -> dict:
        resp.raise_for_status()
        resp = xmltodict.parse(resp.text)
        # TODO Not fully tested.
        if len(resp.keys()) == 1:
            body = resp[next(iter(resp))]
            if len(body.keys()) == 1:
                if 'Messages' in body:
                    raise ValueError(body['Messages']['Message']['description'])
        if 'Error' in resp:
            raise ValueError(resp['Error']['message'])
        return resp

    #
    #
    #
    def __perform_request(self, request_type: str, api_url: str, payload: dict) -> dict:
        headers = {'Content-Type': 'application/xml'}
        payload = xmltodict.unparse(payload, encoding='utf-8')
        resp = None
        if request_type == 'post':
            resp = self.__session.post(api_url, data=payload, headers=headers)
        if request_type == 'put':
            resp = self.__session.put(api_url, data=payload, headers=headers)
        if resp is not None:
            resp.raise_for_status()
            resp = xmltodict.parse(resp.text)
            if 'Error' in resp:
                raise ValueError(resp['Error']['message'])
        else:
            raise ValueError('__perform_request: invalid value in request_type.')
        return resp

    #
    #
    #
    def __generate_order_preview(self, **kwargs) -> int:
        self.__check_order(**kwargs)
        api_url = self.__get_url('accounts/' + kwargs['accountId'] + '/orders/preview')
        payload = self.__build_order_payload(order_type='PreviewOrderRequest', **kwargs)

        resp = self.__perform_request(request_type='post', api_url=api_url, payload=payload)
        return int(resp['PreviewOrderResponse']['PreviewIds']['previewId'])

    #
    #
    #
    def __generate_change_order_preview(self, **kwargs) -> int:
        self.__check_order(**kwargs)
        api_url = self.__get_url('accounts/' + kwargs['accountId'] + '/orders/' + str(kwargs['orderId']) + '/change/preview')
        payload = self.__build_order_payload(order_type='PreviewOrderRequest', **kwargs)

        resp = self.__perform_request(request_type='put', api_url=api_url, payload=payload)
        return int(resp['PreviewOrderResponse']['PreviewIds']['previewId'])

    #
    #
    #
    def place_equity_order(self, **kwargs) -> int:
        """Places an equity order.

        Args:
            accountId: str
            symbol: str
            orderAction: BUY or SELL.
            clientOrderId: str
            priceType: MARKET, LIMIT, or STOP.
            limitPrice: float
            stopPrice: float
            quantity: int
            marketSession: REGULAR or EXTENDED.
            orderTerm: GOOD_UNTIL_CANCEL
            prev_order_id: int

        Returns:
            Order number.
        """
        self.__check_order(**kwargs)

        if 'prev_order_id' in kwargs:
            prev_order_id = kwargs.pop('prev_order_id')
            if prev_order_id is not None:
                kwargs['orderId'] = prev_order_id
                return self.__change_equity_order(**kwargs)

        if 'previewId' not in kwargs:
            kwargs['previewId'] = self.__generate_order_preview(**kwargs)

        api_url = self.__get_url('accounts/' + kwargs['accountId'] + '/orders/place')
        payload = self.__build_order_payload(order_type='PlaceOrderRequest', **kwargs)

        resp = self.__perform_request(request_type='post', api_url=api_url, payload=payload)
        return int(resp['PlaceOrderResponse']['OrderIds']['orderId'])

    #
    #
    #
    def __change_equity_order(self, **kwargs) -> int:
        self.__check_order(**kwargs)

        if 'previewId' not in kwargs:
            kwargs['previewId'] = self.__generate_change_order_preview(**kwargs)

        api_url = self.__get_url('accounts/' + kwargs['accountId'] + '/orders/' + str(kwargs['orderId']) + '/change/place')
        payload = self.__build_order_payload(order_type='PlaceOrderRequest', **kwargs)

        resp = self.__perform_request(request_type='put', api_url=api_url, payload=payload)
        return int(resp['PlaceOrderResponse']['OrderIds']['orderId'])

    #
    #
    #
    def cancel_order(self, account_id: str, order_id: int) -> str:
        """Cancels an order.

        Args:
            account_id: Id of the account where the request has to be performed.
            order_id: Id of the order to cancel.

        Returns:
            Confirmation message.
        """
        api_url = self.__get_url('accounts/' + account_id + '/orders/cancel')
        payload = {'CancelOrderRequest': {'orderId': order_id}}

        resp = self.__perform_request(request_type='put', api_url=api_url, payload=payload)
        return resp['CancelOrderResponse']['Messages']['Message']['description']
