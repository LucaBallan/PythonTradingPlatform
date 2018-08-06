from typing import Tuple, List, Optional
from requests_oauthlib import OAuth1Session


#
#
#
class LowLevelEtradeAuthorization:
    auth_session = None

    def __init__(self):
        pass

    def get_request_token(self, consumer_key, consumer_secret, callback_uri='oob'):
        self.auth_session = OAuth1Session(consumer_key, consumer_secret, callback_uri=callback_uri, signature_type='AUTH_HEADER')
        self.auth_session.fetch_request_token(r'https://etws.etrade.com/oauth/request_token')
        authorization_url = self.auth_session.authorization_url(r'https://us.etrade.com/e/t/etws/authorize')
        a_key = self.auth_session.parse_authorization_response(authorization_url)
        return '%s?key=%s&token=%s' % (r'https://us.etrade.com/e/t/etws/authorize', consumer_key, a_key['oauth_token'])

    def get_access_token(self, verifier):
        return self.auth_session.fetch_access_token(r'https://etws.etrade.com/oauth/access_token', verifier=verifier)


#
#
#
class LowLevelEtradeApi:
    base_url_dev = None
    base_url_prod = None
    session = None

    #
    #
    #
    def __init__(self, session):
        self.base_url_dev = r'https://etwssandbox.etrade.com'
        self.base_url_prod = r'https://etws.etrade.com'
        self.session = session

    #
    #
    #
    def get_url(self, dev, topic, command):
        if dev:
            return self.base_url_dev + r'/' + topic + r'/sandbox/rest/' + command
        else:
            return self.base_url_prod + r'/' + topic + r'/rest/' + command

    def get_base_url(self, dev):
        if dev:
            return self.base_url_dev
        else:
            return self.base_url_prod

    #
    #
    #
    def revoke_access_token(self) -> None:
        resp = self.session.get(self.base_url_prod + r'/oauth/revoke_access_token')
        resp.raise_for_status()

    #
    #
    #
    def get_quote(self, symbols, intraday, dev) -> List[Tuple[str, dict]]:
        """
            [ (symbol_name, symbol_data) ]
        """
        if len(symbols) > 25:
            raise ValueError('Too many symbols to quote.')

        api_url = self.get_url(dev, r'market', r'quote/' + ','.join(symbols) + '.json')

        params = {'detailFlag': 'ALL'} if not intraday else {'detailFlag': 'INTRADAY'}

        req = self.session.get(api_url, params=params)
        req.raise_for_status()

        ret = req.json()
        a = ret['quoteResponse']['quoteData']
        if 'errorMessage' in a:
            raise ValueError(a['errorMessage'])
        if not intraday:
            if isinstance(a, dict):
                return [(a['product']['symbol'], a['all'])]
            else:
                return [(x['product']['symbol'], x['all']) for x in a]
        else:
            if isinstance(a, dict):
                return [(a['product']['symbol'], a['intraday'])]
            else:
                return [(x['product']['symbol'], x['intraday']) for x in a]

    #
    #
    #
    def list_orders(self, account_id, count, marker, dev) -> Tuple[List[dict], Optional[str], int]:
        api_url = self.get_url(dev, r'order', r'orderlist/' + str(account_id) + '.json')

        params = {'count': count}
        if marker is not None:
            params['marker'] = marker

        req = self.session.get(api_url, params=params)
        req.raise_for_status()

        req = req.json()['GetOrderListResponse']['orderListResponse']
        next_marker = None
        if 'marker' in req:
            if len(req['marker']) != 0:
                next_marker = req['marker']
        if int(req['count']) == 0:
            return [], next_marker, 0

        order_list = req['orderDetails']

        if not isinstance(order_list, list):
            order_list = [order_list]

        order_data = []
        not_parsed = 0
        for o in order_list:
            if 'order' not in o:
                not_parsed += 1
                continue
            o = o['order']
            #
            order_info = {'orderId': o['orderId']}

            #
            leg_details = o['legDetails'] if isinstance(o['legDetails'], list) else [o['legDetails']]

            #
            order_info['multipleLegs'] = True if len(leg_details) > 1 else False
            leg_details = leg_details[0]

            order_info['orderAction'] = leg_details['orderAction']
            order_info['symbol'] = leg_details['symbolInfo']['symbol']
            order_info['orderStatus'] = o['orderStatus']
            if order_info['orderStatus'] == 'EXECUTED':
                order_info['executedPrice'] = leg_details['executedPrice']
                order_info['filledQuantity'] = leg_details['filledQuantity']
            if order_info['orderStatus'] == 'OPEN':
                order_info['priceType'] = o['priceType']
                if order_info['priceType'] == 'LIMIT':
                    order_info['limitPrice'] = o['limitPrice']
                if order_info['priceType'] == 'STOP':
                    order_info['stopPrice'] = o['stopPrice']
                if order_info['priceType'] == 'STOP_LIMIT':
                    order_info['limitPrice'] = o['limitPrice']
                    order_info['stopPrice'] = o['stopPrice']
            order_info['orderedQuantity'] = leg_details['orderedQuantity']
            order_data.append(order_info)

        return order_data, next_marker, not_parsed

    #
    #
    #
    def get_account_positions(self, account_id, count, marker, dev) -> List[Tuple[str, int, float, float]]:
        """
        return [symbol, qty, currentPrice, costBasis]
        """
        api_url = self.get_url(dev, r'accounts', r'accountpositions/' + str(account_id) + '.json')

        req = self.session.get(api_url, params={'count': count, 'marker': marker})
        req.raise_for_status()

        positions = req.json()['json.accountPositionsResponse']['response']
        positions = [(p['productId']['symbol'].strip().upper(), int(float(p['qty'])), float(p['currentPrice']), float(p['costBasis'])) for p in positions]
        return positions

    #
    #
    #
    def get_account_balance(self, account_id, dev) -> Tuple[float, float, float]:
        api_url = self.get_url(dev, r'accounts', r'accountbalance/' + str(account_id) + '.json')

        req = self.session.get(api_url)
        req.raise_for_status()

        info = req.json()['json.accountBalanceResponse']
        return float(info['accountBalance']['netAccountValue']), float(info['cashAccountBalance']['settledCashForInvestment']), float(info['cashAccountBalance']['unSettledCashForInvestment'])

    #
    #
    #
    def list_accounts(self, dev) -> List[Tuple[int, int, str, int]]:
        api_url = self.get_url(dev, r'accounts', r'accountlist.json')

        req = self.session.get(api_url)
        req.raise_for_status()

        accounts = req.json()['json.accountListResponse']['response']
        accounts = [(i, accounts[i]['accountId'], accounts[i]['accountDesc'], int(float(accounts[i]['netAccountValue']) / 1000)) for i in range(len(accounts))]
        return accounts

    #
    #
    #
    def place_equity_order(self, dev, **kwargs) -> int:
        required = ['accountId', 'symbol', 'orderAction', 'clientOrderId', 'priceType', 'quantity', 'orderTerm', 'marketSession']
        for r in required:
            if r not in kwargs:
                raise ValueError(r + ' is required to place an order.')

        if kwargs['priceType'] == 'STOP' and 'stopPrice' not in kwargs:
            raise ValueError('stopPrice is required to place an order.')
        if kwargs['priceType'] == 'LIMIT' and 'limitPrice' not in kwargs:
            raise ValueError('limitPrice is required to place an order.')
        if kwargs['priceType'] == 'STOP_LIMIT' and ('limitPrice' not in kwargs or 'stopPrice' not in kwargs):
            raise ValueError('limitPrice and stopPrice are required to place an order.')

        change_order = False
        if 'prev_order_id' in kwargs:
            if kwargs['prev_order_id'] is not None:
                change_order = True
                kwargs['orderNum'] = kwargs['prev_order_id']
            kwargs.pop('prev_order_id')

        #
        if not change_order:
            json_data = dict()
            json_data['PlaceEquityOrder'] = {'-xmlns': self.get_base_url(dev)}
            json_data['PlaceEquityOrder']['EquityOrderRequest'] = kwargs

            api_url = self.get_url(dev, r'order', r'placeequityorder.json')

            req = self.session.post(api_url, json=json_data)
            req.raise_for_status()

            req = req.json()
            if 'Error' in req:
                raise ValueError(req['Error']['message'])
            return int(req['PlaceEquityOrderResponse']['EquityOrderResponse']['orderNum'])

        else:
            json_data = dict()
            json_data['placeChangeEquityOrder'] = {'-xmlns': self.get_base_url(dev)}
            json_data['placeChangeEquityOrder']['changeEquityOrderRequest'] = kwargs

            api_url = self.get_url(dev, r'order', r'placechangeequityorder.json')

            req = self.session.post(api_url, json=json_data)
            req.raise_for_status()

            req = req.json()
            if 'Error' in req:
                raise ValueError(req['Error']['message'])
            return int(req['placeChangeEquityOrderResponse']['equityOrderResponse']['orderNum'])

    #
    #
    #
    def cancel_order(self, account_id, order_num, dev) -> str:
        api_url = self.get_url(dev, r'order', r'cancelorder.json')

        json_data = dict()
        json_data['cancelOrder'] = dict()
        json_data['cancelOrder']['-xmlns'] = self.get_base_url(dev)
        json_data['cancelOrder']['cancelOrderRequest'] = {'accountId': account_id, 'orderNum': order_num}

        req = self.session.post(api_url, json=json_data)
        req.raise_for_status()

        return req.json()['cancelOrderResponse']['cancelResponse']['resultMessage']
